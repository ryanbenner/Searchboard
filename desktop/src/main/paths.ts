import { accessSync, constants } from 'node:fs'
import { delimiter, join } from 'node:path'

export function which(cmd: string): string | null {
  const exts = process.platform === 'win32' ? ['.exe', '.cmd', '.bat'] : ['']
  for (const dir of (process.env.PATH ?? '').split(delimiter)) {
    for (const ext of exts) {
      const p = join(dir, cmd + ext)
      try {
        accessSync(p, constants.X_OK)
        return p
      } catch {
        /* keep looking */
      }
    }
  }
  return null
}
