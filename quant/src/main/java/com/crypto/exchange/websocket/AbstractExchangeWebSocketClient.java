package com.crypto.exchange.websocket;

import lombok.extern.slf4j.Slf4j;
import org.java_websocket.client.WebSocketClient;
import org.java_websocket.handshake.ServerHandshake;

import java.net.URI;
import java.util.concurrent.Executors;
import java.util.concurrent.ScheduledExecutorService;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.atomic.AtomicBoolean;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.function.Consumer;

/**
 * 抽象 WebSocket 客户端基类
 * 提供自动重连、心跳保活、消息回调等通用功能
 */
@Slf4j
public abstract class AbstractExchangeWebSocketClient {

    protected volatile WebSocketClient webSocketClient;
    protected final String wsUrl;
    protected final String name;
    protected final Consumer<String> messageHandler;

    private final AtomicBoolean connected = new AtomicBoolean(false);
    private final AtomicBoolean shouldReconnect = new AtomicBoolean(true);
    private final AtomicInteger reconnectCount = new AtomicInteger(0);

    private static final int MAX_RECONNECT_ATTEMPTS = 50;
    private static final long INITIAL_RECONNECT_DELAY_MS = 1000;
    private static final long MAX_RECONNECT_DELAY_MS = 60000;

    private final ScheduledExecutorService scheduler;

    protected AbstractExchangeWebSocketClient(String wsUrl, String name, Consumer<String> messageHandler) {
        this.wsUrl = wsUrl;
        this.name = name;
        this.messageHandler = messageHandler;
        this.scheduler = Executors.newSingleThreadScheduledExecutor(
                r -> {
                    Thread t = new Thread(r);
                    t.setDaemon(true);
                    t.setName("ws-reconnect-" + name);
                    return t;
                });
    }

    /**
     * 连接并发送订阅消息
     */
    public void connect() {
        shouldReconnect.set(true);
        reconnectCount.set(0);
        doConnect();
    }

    /**
     * 断开连接
     */
    public void disconnect() {
        shouldReconnect.set(false);
        scheduler.shutdownNow();
        if (webSocketClient != null) {
            try {
                webSocketClient.closeBlocking();
            } catch (InterruptedException e) {
                Thread.currentThread().interrupt();
            }
        }
        connected.set(false);
        log.info("[{}] WebSocket已断开", name);
    }

    /**
     * 发送文本消息
     */
    public void send(String message) {
        if (webSocketClient != null && connected.get()) {
            webSocketClient.send(message);
        } else {
            log.warn("[{}] WebSocket未连接，无法发送消息", name);
        }
    }

    public boolean isConnected() {
        return connected.get();
    }

    /**
     * 子类实现：返回订阅消息JSON
     */
    protected abstract String buildSubscribeMessage();

    /**
     * 子类实现：处理心跳响应（如Ping/Pong）
     */
    protected abstract void handlePingPong(String message);

    /**
     * 子类可选重写：连接成功后的额外操作
     */
    protected void onConnected() {
        // 默认空实现
    }

    private void doConnect() {
        try {
            URI uri = new URI(wsUrl);
            webSocketClient = new WebSocketClient(uri) {
                @Override
                public void onOpen(ServerHandshake handshake) {
                    connected.set(true);
                    reconnectCount.set(0);
                    log.info("[{}] WebSocket连接成功: {}", name, wsUrl);

                    // 发送订阅消息
                    String subscribeMsg = buildSubscribeMessage();
                    if (subscribeMsg != null && !subscribeMsg.isEmpty()) {
                        send(subscribeMsg);
                        log.info("[{}] 已发送订阅消息", name);
                    }

                    onConnected();
                }

                @Override
                public void onMessage(String message) {
                    try {
                        // 先检查是否是心跳消息
                        handlePingPong(message);
                        // 调用业务处理回调
                        if (messageHandler != null) {
                            messageHandler.accept(message);
                        }
                    } catch (Exception e) {
                        log.error("[{}] 处理WebSocket消息异常", name, e);
                    }
                }

                @Override
                public void onClose(int code, String reason, boolean remote) {
                    connected.set(false);
                    log.warn("[{}] WebSocket连接关闭: code={}, reason={}, remote={}",
                            name, code, reason, remote);
                    scheduleReconnect();
                }

                @Override
                public void onError(Exception ex) {
                    log.error("[{}] WebSocket异常", name, ex);
                }
            };

            webSocketClient.setConnectionLostTimeout(30);
            webSocketClient.connect();

        } catch (Exception e) {
            log.error("[{}] WebSocket连接失败: url={}", name, wsUrl, e);
            scheduleReconnect();
        }
    }

    private void scheduleReconnect() {
        if (!shouldReconnect.get()) {
            return;
        }

        int attempt = reconnectCount.incrementAndGet();
        if (attempt > MAX_RECONNECT_ATTEMPTS) {
            log.error("[{}] WebSocket重连次数超限({}次)，停止重连", name, MAX_RECONNECT_ATTEMPTS);
            return;
        }

        // 指数退避
        long delay = Math.min(
                INITIAL_RECONNECT_DELAY_MS * (1L << Math.min(attempt - 1, 6)),
                MAX_RECONNECT_DELAY_MS
        );

        log.info("[{}] 将在{}ms后尝试第{}次重连", name, delay, attempt);

        try {
            scheduler.schedule(this::doConnect, delay, TimeUnit.MILLISECONDS);
        } catch (Exception e) {
            log.error("[{}] 调度重连失败", name, e);
        }
    }
}
