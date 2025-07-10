import { GET, POST } from '@/app/api/projects/route'
import fs from 'fs'
import path from 'path'
import { NextRequest } from 'next/server'

// Mock fs module
jest.mock('fs')
jest.mock('path')

const mockFs = fs as jest.Mocked<typeof fs>
const mockPath = path as jest.Mocked<typeof path>

describe('/api/projects', () => {
  beforeEach(() => {
    jest.clearAllMocks()
    mockPath.resolve.mockImplementation((...args) => args.join('/'))
    mockPath.join.mockImplementation((...args) => args.join('/'))
  })

  describe('GET', () => {
    it('should return empty array when no projects exist', async () => {
      mockFs.existsSync.mockReturnValue(false)
      
      const request = new NextRequest('http://localhost/api/projects')
      const response = await GET(request)
      const data = await response.json()

      expect(response.status).toBe(200)
      expect(data).toEqual({
        projects: [],
        totalProjects: 0
      })
    })

    it('should return all projects when metadata directory exists', async () => {
      const mockProjects = [
        'project-1.json',
        'project-2.json',
        'not-json.txt' // Should be filtered out
      ]
      
      const mockMetadata1 = {
        name: 'Project 1',
        status: 'active',
        tags: ['web-app'],
        dependencies: ['react', 'next.js'],
        estimated_completion: '2024-01-01'
      }
      
      const mockMetadata2 = {
        name: 'Project 2',
        status: 'planning',
        tags: ['script'],
        dependencies: ['python'],
        estimated_completion: '2024-02-01'
      }

      mockFs.existsSync.mockReturnValue(true)
      mockFs.readdirSync.mockReturnValue(mockProjects as any)
      mockFs.readFileSync
        .mockReturnValueOnce(JSON.stringify(mockMetadata1))
        .mockReturnValueOnce(JSON.stringify(mockMetadata2))

      const request = new NextRequest('http://localhost/api/projects')
      const response = await GET(request)
      const data = await response.json()

      expect(response.status).toBe(200)
      expect(data.totalProjects).toBe(2)
      expect(data.projects).toHaveLength(2)
      expect(data.projects[0]).toMatchObject({
        project_id: 'project-1',
        name: 'Project 1',
        project_type: 'application',
        status: 'active'
      })
    })

    it('should handle file read errors gracefully', async () => {
      mockFs.existsSync.mockReturnValue(true)
      mockFs.readdirSync.mockReturnValue(['error-project.json'] as any)
      mockFs.readFileSync.mockImplementation(() => {
        throw new Error('File read error')
      })

      const request = new NextRequest('http://localhost/api/projects')
      const response = await GET(request)
      const data = await response.json()

      expect(response.status).toBe(200)
      expect(data.projects).toEqual([])
      expect(data.totalProjects).toBe(0)
    })
  })

  describe('POST', () => {
    it('should create a new project successfully', async () => {
      const newProject = {
        name: 'New Project',
        project_type: 'application',
        status: 'planning',
        tech_stack: ['typescript', 'react']
      }

      mockFs.existsSync.mockReturnValue(true)
      mockFs.writeFileSync.mockImplementation(() => {})

      const request = new NextRequest('http://localhost/api/projects', {
        method: 'POST',
        body: JSON.stringify(newProject)
      })
      
      const response = await POST(request)
      const data = await response.json()

      expect(response.status).toBe(201)
      expect(data.success).toBe(true)
      expect(data.project.name).toBe(newProject.name)
      expect(data.project.project_id).toBeDefined()
      expect(mockFs.writeFileSync).toHaveBeenCalled()
    })

    it('should reject project creation with missing required fields', async () => {
      const invalidProject = {
        project_type: 'application'
        // Missing name
      }

      const request = new NextRequest('http://localhost/api/projects', {
        method: 'POST',
        body: JSON.stringify(invalidProject)
      })
      
      const response = await POST(request)
      const data = await response.json()

      expect(response.status).toBe(400)
      expect(data.error).toBe('Missing required fields')
    })

    it('should handle directory creation when metadata dir does not exist', async () => {
      const newProject = {
        name: 'New Project',
        project_type: 'application',
        status: 'planning'
      }

      mockFs.existsSync.mockReturnValue(false)
      mockFs.mkdirSync.mockImplementation(() => {})
      mockFs.writeFileSync.mockImplementation(() => {})

      const request = new NextRequest('http://localhost/api/projects', {
        method: 'POST',
        body: JSON.stringify(newProject)
      })
      
      const response = await POST(request)
      
      expect(response.status).toBe(201)
      expect(mockFs.mkdirSync).toHaveBeenCalledWith(
        expect.any(String),
        { recursive: true }
      )
    })

    it('should handle JSON parse errors', async () => {
      const request = new NextRequest('http://localhost/api/projects', {
        method: 'POST',
        body: 'invalid json'
      })
      
      const response = await POST(request)
      const data = await response.json()

      expect(response.status).toBe(500)
      expect(data.error).toBe('Failed to create project')
    })
  })
})