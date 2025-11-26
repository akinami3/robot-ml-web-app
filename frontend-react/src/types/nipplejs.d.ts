// Type definitions for nipplejs
// Project: https://github.com/yoannmoinet/nipplejs
// Definitions by: GitHub Copilot

declare module 'nipplejs' {
  export interface JoystickManagerOptions {
    zone?: HTMLElement
    color?: string
    size?: number
    threshold?: number
    fadeTime?: number
    multitouch?: boolean
    maxNumberOfNipples?: number
    dataOnly?: boolean
    position?: { top?: string; left?: string; right?: string; bottom?: string }
    mode?: 'static' | 'semi' | 'dynamic'
    restJoystick?: boolean
    restOpacity?: number
    lockX?: boolean
    lockY?: boolean
    catchDistance?: number
    shape?: 'circle' | 'square'
    dynamicPage?: boolean
    follow?: boolean
  }

  export interface JoystickOutputData {
    distance: number
    angle: {
      radian: number
      degree: number
    }
    direction?: {
      x: string
      y: string
      angle: string
    }
    force: number
    pressure: number
    position: {
      x: number
      y: number
    }
    instance: any
  }

  export interface EventData {
    type: string
  }

  export interface JoystickManager {
    on(type: string, handler: (evt: EventData, data: JoystickOutputData) => void): void
    off(type: string, handler?: (evt: EventData, data: JoystickOutputData) => void): void
    destroy(): void
    get(id?: number): any
  }

  export function create(options?: JoystickManagerOptions): JoystickManager

  export default {
    create
  }
}
