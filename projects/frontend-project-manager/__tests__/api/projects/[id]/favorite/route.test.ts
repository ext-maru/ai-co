import { NextRequest } from 'next/server'
import { GET, POST } from '@/app/api/projects/[id]/favorite/route'
import fs from 'fs'
import path from 'path'

jest.mock('fs')
jest.mock('path')

const mockFs = fs as jest.Mocked<typeof fs>
const mockPath = path as jest.Mocked<typeof path>

describe('/api/projects/[id]/favorite', () => {
  beforeEach(() => {
    jest.clearAllMocks()
    mockPath.resolve.mockImplementation((...args) => args.join('/'))
    mockPath.join.mockImplementation((...args) => args.join('/'))
  })

  describe('POST', () => {
    it('should add project to favorites when not favorited', async () => {
      const projectId = 'test-project'
      const userId = 'test-user'
      
      mockFs.existsSync.mockReturnValue(true)
      mockFs.readFileSync.mockReturnValue(JSON.stringify({
        'other-user': ['project-1']
      }))
      mockFs.writeFileSync.mockImplementation(() => {})

      const request = new NextRequest('http://localhost/api/projects/test-project/favorite', {
        method: 'POST',
        body: JSON.stringify({ user_id: userId })
      })
      
      const response = await POST(request, { params: { id: projectId } })
      const data = await response.json()

      expect(response.status).toBe(200)
      expect(data.success).toBe(true)
      expect(data.action).toBe('added')
      expect(data.is_favorite).toBe(true)
      expect(data.project_id).toBe(projectId)
      
      // Verify file write
      expect(mockFs.writeFileSync).toHaveBeenCalledWith(
        expect.any(String),
        expect.stringContaining(projectId)
      )
    })

    it('should remove project from favorites when already favorited', async () => {
      const projectId = 'test-project'
      const userId = 'test-user'
      
      mockFs.existsSync.mockReturnValue(true)
      mockFs.readFileSync.mockReturnValue(JSON.stringify({
        'test-user': ['test-project', 'other-project']
      }))
      mockFs.writeFileSync.mockImplementation(() => {})

      const request = new NextRequest('http://localhost/api/projects/test-project/favorite', {
        method: 'POST',
        body: JSON.stringify({ user_id: userId })
      })
      
      const response = await POST(request, { params: { id: projectId } })
      const data = await response.json()

      expect(response.status).toBe(200)
      expect(data.success).toBe(true)
      expect(data.action).toBe('removed')
      expect(data.is_favorite).toBe(false)
      
      // Verify the project was removed from favorites
      const writeCall = mockFs.writeFileSync.mock.calls[0]
      const writtenData = JSON.parse(writeCall[1] as string)
      expect(writtenData[userId]).not.toContain(projectId)
    })

    it('should handle new user with no existing favorites', async () => {
      const projectId = 'test-project'
      const userId = 'new-user'
      
      mockFs.existsSync.mockReturnValue(false)
      mockFs.mkdirSync.mockImplementation(() => {})
      mockFs.writeFileSync.mockImplementation(() => {})

      const request = new NextRequest('http://localhost/api/projects/test-project/favorite', {
        method: 'POST',
        body: JSON.stringify({ user_id: userId })
      })
      
      const response = await POST(request, { params: { id: projectId } })
      const data = await response.json()

      expect(response.status).toBe(200)
      expect(data.action).toBe('added')
      expect(mockFs.mkdirSync).toHaveBeenCalled()
    })

    it('should use default user when user_id not provided', async () => {
      mockFs.existsSync.mockReturnValue(true)
      mockFs.readFileSync.mockReturnValue(JSON.stringify({}))
      mockFs.writeFileSync.mockImplementation(() => {})

      const request = new NextRequest('http://localhost/api/projects/test-project/favorite', {
        method: 'POST',
        body: JSON.stringify({})
      })
      
      const response = await POST(request, { params: { id: 'test-project' } })
      const data = await response.json()

      expect(response.status).toBe(200)
      expect(data.success).toBe(true)
      
      const writeCall = mockFs.writeFileSync.mock.calls[0]
      const writtenData = JSON.parse(writeCall[1] as string)
      expect(writtenData['default_user']).toContain('test-project')
    })

    it('should handle file system errors', async () => {
      mockFs.existsSync.mockReturnValue(true)
      mockFs.readFileSync.mockImplementation(() => {
        throw new Error('Permission denied')
      })

      const request = new NextRequest('http://localhost/api/projects/test-project/favorite', {
        method: 'POST',
        body: JSON.stringify({ user_id: 'test-user' })
      })
      
      const response = await POST(request, { params: { id: 'test-project' } })
      const data = await response.json()

      expect(response.status).toBe(500)
      expect(data.error).toBe('Failed to toggle favorite')
    })
  })

  describe('GET', () => {
    it('should return favorite status for a project', async () => {
      const projectId = 'test-project'
      const userId = 'test-user'
      
      mockFs.existsSync.mockReturnValue(true)
      mockFs.readFileSync.mockReturnValue(JSON.stringify({
        'test-user': ['test-project', 'other-project']
      }))

      const request = new NextRequest(`http://localhost/api/projects/test-project/favorite?user_id=${userId}`)
      const response = await GET(request, { params: { id: projectId } })
      const data = await response.json()

      expect(response.status).toBe(200)
      expect(data.project_id).toBe(projectId)
      expect(data.user_id).toBe(userId)
      expect(data.is_favorite).toBe(true)
    })

    it('should return false when project is not favorited', async () => {
      const projectId = 'test-project'
      const userId = 'test-user'
      
      mockFs.existsSync.mockReturnValue(true)
      mockFs.readFileSync.mockReturnValue(JSON.stringify({
        'test-user': ['other-project']
      }))

      const request = new NextRequest(`http://localhost/api/projects/test-project/favorite?user_id=${userId}`)
      const response = await GET(request, { params: { id: projectId } })
      const data = await response.json()

      expect(response.status).toBe(200)
      expect(data.is_favorite).toBe(false)
    })

    it('should use default user when user_id not provided', async () => {
      mockFs.existsSync.mockReturnValue(true)
      mockFs.readFileSync.mockReturnValue(JSON.stringify({
        'default_user': ['test-project']
      }))

      const request = new NextRequest('http://localhost/api/projects/test-project/favorite')
      const response = await GET(request, { params: { id: 'test-project' } })
      const data = await response.json()

      expect(response.status).toBe(200)
      expect(data.user_id).toBe('default_user')
      expect(data.is_favorite).toBe(true)
    })

    it('should handle missing favorites file', async () => {
      mockFs.existsSync.mockReturnValue(false)

      const request = new NextRequest('http://localhost/api/projects/test-project/favorite')
      const response = await GET(request, { params: { id: 'test-project' } })
      const data = await response.json()

      expect(response.status).toBe(200)
      expect(data.is_favorite).toBe(false)
    })
  })
})