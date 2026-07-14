/// <reference types="vite/client" />

declare module '*.vue' {
  import type { DefineComponent } from 'vue'
  const component: DefineComponent<object, object, unknown>
  export default component
}

declare module '@element-plus/icons-vue' {
  import type { DefineComponent } from 'vue'
  const icons: Record<string, DefineComponent<object, object, unknown>>
  export = icons
  export const ArrowLeft: DefineComponent<object, object, unknown>
  export const Document: DefineComponent<object, object, unknown>
  export const Printer: DefineComponent<object, object, unknown>
  export const Refresh: DefineComponent<object, object, unknown>
  export const Van: DefineComponent<object, object, unknown>
  export const VideoCamera: DefineComponent<object, object, unknown>
  export const Tools: DefineComponent<object, object, unknown>
  export const Monitor: DefineComponent<object, object, unknown>
  export const User: DefineComponent<object, object, unknown>
}
