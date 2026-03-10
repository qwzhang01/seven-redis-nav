import {defineStore} from 'pinia'
import {ref, computed} from 'vue'
import * as userApi from '@/utils/userApi'
import {setToken, clearToken, setRefreshToken} from '@/utils/request'
import type {UserProfile, LoginRequest, RegisterRequest} from '@/utils/userApi'
import {MessagePlugin} from "tdesign-vue-next";

export interface UserInfo {
    id: string
    username: string
    email: string
    avatar?: string
    role: 'user' | 'admin'
    createdAt: string
    totalAssets?: number
    runningStrategies?: number
    followingSignals?: number
    totalReturn?: number
}

/**
 * 将API返回的用户信息转换为前端使用的格式
 */
function transformUserProfile(profile: UserProfile): UserInfo {
    return {
        id: profile.id,
        username: profile.username,
        email: profile.email,
        avatar: profile.avatar_url || '',
        role: profile.user_type === 'admin' ? 'admin' : 'user',
        createdAt: profile.create_time || profile.registration_time,
    }
}

export const useAuthStore = defineStore('auth', () => {
    const token = ref<string | null>(localStorage.getItem('qm_token'))
    const user = ref<UserInfo | null>(null)

    const isLoggedIn = computed(() => !!token.value)
    const isAdmin = computed(() => user.value?.role === 'admin')

    /**
     * 初始化：从localStorage恢复用户信息
     */
    function init() {
        const saved = localStorage.getItem('qm_user')
        if (saved && token.value) {
            try {
                user.value = JSON.parse(saved)
            } catch {
                logout()
            }
        }
    }

    /**
     * 用户登录
     */
    async function login(username: string, password: string): Promise<UserInfo> {
        const loginData: LoginRequest = {username, password}
        const response = await userApi.login(loginData)
        if (response.access_token) {
            // 保存 access_token
            const accessToken = response.access_token
            token.value = accessToken
            setToken(accessToken)

            // 保存 refresh_token
            if (response.refresh_token) {
                setRefreshToken(response.refresh_token)
            }

            // 转换并保存用户信息
            const userInfo = transformUserProfile(response.user)
            user.value = userInfo
            localStorage.setItem('qm_user', JSON.stringify(userInfo))

            return userInfo
        }
        token.value = null
        user.value = null
        throw Error(response.remark);
    }

    /**
     * 用户注册
     */
    async function register(data: RegisterRequest): Promise<UserInfo> {
        try {
            const profile = await userApi.register(data)
            if (profile) {
                await MessagePlugin.warning(profile as string)
                return {} as UserInfo;
            } else {
                // 注册成功后自动登录
                const user = await login(data.username, data.password)
                if (user) {
                    await MessagePlugin.success('注册成功，正在跳转...')
                }
                return user
            }
        } catch (error) {
            throw error
        }
    }

    /**
     * 更新用户信息
     */
    async function updateProfile(data: {
        nickname?: string
        email?: string
        phone?: string
        avatar_url?: string
    }): Promise<UserInfo> {
        try {
            const profile = await userApi.updateProfile(data)
            const userInfo = transformUserProfile(profile)
            user.value = userInfo
            localStorage.setItem('qm_user', JSON.stringify(userInfo))
            return userInfo
        } catch (error) {
            throw error
        }
    }

    /**
     * 修改密码
     */
    async function changePassword(oldPassword: string, newPassword: string): Promise<void> {
        try {
            await userApi.changePassword({
                old_password: oldPassword,
                new_password: newPassword,
            })
        } catch (error) {
            throw error
        }
    }

    /**
     * 用户登出
     */
    function logout() {
        token.value = null
        user.value = null
        clearToken()
    }

    // 初始化
    init()

    return {
        token,
        user,
        isLoggedIn,
        isAdmin,
        login,
        register,
        logout,
        updateProfile,
        changePassword,
    }
})
