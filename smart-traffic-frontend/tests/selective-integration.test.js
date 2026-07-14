import test from 'node:test'
import assert from 'node:assert/strict'
import { readFile } from 'node:fs/promises'

const source = path => readFile(new URL(path, import.meta.url), 'utf8')

test('profile edits backend contact fields and uses role avatars', async () => {
  const profile = await source('../src/views/Profile.vue')
  assert.match(profile, /form\.email/)
  assert.match(profile, /form\.phone/)
  assert.match(profile, /updateProfile\(\{ phone: form\.phone, email: form\.email \}\)/)
  assert.match(profile, /\/images\/admin\.jpg/)
  assert.match(profile, /\/images\/reviewer\.jpg/)
  assert.match(profile, /\/images\/citizen\.jpg/)
  assert.match(profile, /userStore\.logout\(\)/)
  assert.match(profile, /router\.push\('\/login'\)/)
})
