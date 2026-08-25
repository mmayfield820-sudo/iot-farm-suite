import { defineStore } from 'pinia'
import { computed, ref } from 'vue'

export const useMqttStore = defineStore('mqtt', () => {
  const connected = ref(false)
  const connecting = ref(false)
  const lastMessage = ref(null)
  const messageCount = ref(0)
  const transport = ref(null)
  const subscriptions = new Map()

  const connectionLabel = computed(() => connecting.value ? '连接中' : connected.value ? '已连接' : '未连接')

  function setConnected(status) {
    connected.value = Boolean(status)
    connecting.value = false
  }

  function subscribe(topic, handler) {
    if (!subscriptions.has(topic)) subscriptions.set(topic, new Set())
    subscriptions.get(topic).add(handler)
    return () => subscriptions.get(topic)?.delete(handler)
  }

  function receive(topic, payload) {
    const message = { topic, payload, receivedAt: new Date().toISOString() }
    lastMessage.value = message
    messageCount.value += 1
    subscriptions.get(topic)?.forEach((handler) => handler(message))
    subscriptions.forEach((handlers, pattern) => {
      if (pattern.endsWith('/+') && topic.startsWith(pattern.slice(0, -1))) {
        handlers.forEach((handler) => handler(message))
      }
    })
    return message
  }

  async function initRealtime(adapter) {
    if (!adapter) {
      setConnected(true)
      return { mode: 'mock', disconnect: () => setConnected(false) }
    }
    connecting.value = true
    transport.value = adapter
    try {
      await adapter.connect({ onMessage: receive, onStatus: setConnected })
      setConnected(true)
      return adapter
    } catch (error) {
      setConnected(false)
      throw error
    }
  }

  async function publish(topic, payload) {
    if (!connected.value) throw new Error('实时通信未连接')
    if (transport.value?.publish) return transport.value.publish(topic, payload)
    return { accepted: true, topic, payload, mode: 'mock' }
  }

  function disconnect() {
    transport.value?.disconnect?.()
    transport.value = null
    setConnected(false)
  }

  return { connected, connecting, connectionLabel, lastMessage, messageCount, setConnected, subscribe, receive, initRealtime, publish, disconnect }
})
