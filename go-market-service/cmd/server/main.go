// Package main 行情处理系统启动入口
package main

import (
	"context"
	"flag"
	"net/http"
	"os"
	"os/signal"
	"syscall"
	"time"

	"github.com/gin-gonic/gin"
	"go.uber.org/zap"

	"github.com/quant/go-market-service/internal/config"
	"github.com/quant/go-market-service/internal/handler"
	"github.com/quant/go-market-service/internal/middleware"
	"github.com/quant/go-market-service/internal/service"
	"github.com/quant/go-market-service/internal/storage"
	"github.com/quant/go-market-service/pkg/logger"
)

func main() {
	// 命令行参数
	configPath := flag.String("config", "configs/config.yaml", "配置文件路径")
	flag.Parse()

	// 初始化配置
	cfg, err := config.Load(*configPath)
	if err != nil {
		panic("加载配置失败: " + err.Error())
	}

	// 初始化日志
	log := logger.New(cfg.Log)
	defer log.Sync()

	log.Info("启动行情处理系统",
		zap.String("version", "1.0.0"),
		zap.String("env", cfg.Env),
	)

	// 初始化存储
	store, err := storage.New(cfg.Storage, log)
	if err != nil {
		log.Fatal("初始化存储失败", zap.Error(err))
	}
	defer store.Close()

	// 初始化服务
	svc := service.New(cfg, store, log)

	// 启动行情采集
	ctx, cancel := context.WithCancel(context.Background())
	defer cancel()

	if err := svc.Start(ctx); err != nil {
		log.Fatal("启动服务失败", zap.Error(err))
	}

	// 初始化HTTP服务
	if cfg.Env == "production" {
		gin.SetMode(gin.ReleaseMode)
	}

	router := gin.New()
	router.Use(
		middleware.Logger(log),
		middleware.Recovery(log),
		middleware.Cors(),
	)

	// 注册路由
	h := handler.New(svc, log)
	h.RegisterRoutes(router)

	// 启动HTTP服务
	srv := &http.Server{
		Addr:         cfg.Server.Addr,
		Handler:      router,
		ReadTimeout:  time.Duration(cfg.Server.ReadTimeout) * time.Second,
		WriteTimeout: time.Duration(cfg.Server.WriteTimeout) * time.Second,
	}

	go func() {
		log.Info("HTTP服务启动", zap.String("addr", cfg.Server.Addr))
		if err := srv.ListenAndServe(); err != nil && err != http.ErrServerClosed {
			log.Fatal("HTTP服务启动失败", zap.Error(err))
		}
	}()

	// 优雅关闭
	quit := make(chan os.Signal, 1)
	signal.Notify(quit, syscall.SIGINT, syscall.SIGTERM)
	<-quit

	log.Info("正在关闭服务...")

	// 设置关闭超时
	shutdownCtx, shutdownCancel := context.WithTimeout(context.Background(), 30*time.Second)
	defer shutdownCancel()

	// 停止服务
	svc.Stop()

	// 关闭HTTP服务
	if err := srv.Shutdown(shutdownCtx); err != nil {
		log.Error("HTTP服务关闭失败", zap.Error(err))
	}

	log.Info("服务已关闭")
}
