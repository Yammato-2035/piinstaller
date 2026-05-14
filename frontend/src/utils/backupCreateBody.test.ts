import { describe, expect, it } from 'vitest'
import { buildBackupCreateBody } from './backupCreateBody'

describe('buildBackupCreateBody', () => {
  const common = { backupDir: '/media/u/bk', target: 'local', async: true, confirmFullExpert: false }

  it('default recommended maps to profile + recommended', () => {
    expect(buildBackupCreateBody('recommended', common)).toEqual({
      backup_dir: '/media/u/bk',
      target: 'local',
      async: true,
      type: 'profile',
      profile: 'recommended',
    })
  })

  it('full-expert passes confirm flag', () => {
    expect(
      buildBackupCreateBody('full-expert', { ...common, confirmFullExpert: true }),
    ).toMatchObject({ type: 'profile', profile: 'full-expert', confirm_full_expert: true })
  })

  it('incremental keeps legacy type', () => {
    expect(buildBackupCreateBody('incremental', common)).toEqual({
      backup_dir: '/media/u/bk',
      target: 'local',
      async: true,
      type: 'incremental',
    })
  })
})
