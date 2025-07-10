import { NextRequest } from 'next/server'
import { GET } from '@/app/api/projects/[id]/route'
import fs from 'fs'
import path from 'path'

jest.mock('fs')
jest.mock('path')

const mockFs = fs as jest.Mocked<typeof fs>
const mockPath = path as jest.Mocked<typeof path>

describe('/api/projects/[id]', () => {
  beforeEach(() => {
    jest.clearAllMocks()
    mockPath.resolve.mockImplementation((...args) => args.join('/'))
    mockPath.join.mockImplementation((...args) => args.join('/'))
  })

  describe('GET', () => {
    it('should return project details when project exists', async () => {
      const projectId = 'test-project'
      const mockMetadata = {
        name: 'Test Project',
        status: 'active',
        tags: ['web-app', 'next.js'],
        dependencies: ['react', 'typescript'],
        complexity: 'medium',
        business_value: 'high',
        team_members: ['alice', 'bob'],
        description: 'A test project for testing',
        related_projects: ['project-2', 'project-3'],
        planning_start: '2024-01-01',
        actual_start: '2024-01-05',
        estimated_completion: '2024-03-01',
        actual_completion: null,
        deployment_info: {
          environment: 'production',
          url: 'https://test-project.example.com'
        },
        repository: 'https://github.com/example/test-project',
        documentation: '/docs/test-project',
        progress_percentage: 75,
        risk_factors: ['timeline', 'resources'],
        milestones: [
          { name: 'MVP', date: '2024-02-01', completed: true },
          { name: 'Launch', date: '2024-03-01', completed: false }
        ]
      }

      const mockFiles = [
        'src/index.ts',
        'src/components/Header.tsx',
        'package.json',
        'README.md'
      ]

      const mockStructure = {
        name: 'test-project',
        type: 'directory',
        children: [
          {
            name: 'src',
            type: 'directory',
            children: [
              { name: 'index.ts', type: 'file' },
              { name: 'components', type: 'directory', children: [] }
            ]
          }
        ]
      }

      // Mock project exists
      mockFs.existsSync
        .mockReturnValueOnce(true) // metadata file exists
        .mockReturnValueOnce(true) // project directory exists
        .mockReturnValue(false) // for isDirectory checks

      mockFs.readFileSync.mockReturnValue(JSON.stringify(mockMetadata))
      mockFs.readdirSync.mockReturnValue(mockFiles as any)
      mockFs.statSync.mockReturnValue({
        isDirectory: () => false,
        size: 1024
      } as any)

      const request = new NextRequest('http://localhost/api/projects/test-project')
      const response = await GET(request, { params: { id: projectId } })
      const data = await response.json()

      expect(response.status).toBe(200)
      expect(data.project_id).toBe(projectId)
      expect(data.name).toBe(mockMetadata.name)
      expect(data.status).toBe(mockMetadata.status)
      expect(data.project_type).toBe('application')
      expect(data.tech_stack).toEqual(mockMetadata.dependencies)
      expect(data.files).toBeDefined()
      expect(data.file_structure).toBeDefined()
      expect(data.stats).toBeDefined()
      expect(data.stats.total_files).toBeGreaterThan(0)
    })

    it('should return 404 when project metadata does not exist', async () => {
      mockFs.existsSync.mockReturnValue(false)

      const request = new NextRequest('http://localhost/api/projects/non-existent')
      const response = await GET(request, { params: { id: 'non-existent' } })
      const data = await response.json()

      expect(response.status).toBe(404)
      expect(data.error).toBe('Project not found')
    })

    it('should handle project directory not existing gracefully', async () => {
      const mockMetadata = {
        name: 'Test Project',
        status: 'planning',
        tags: ['web-app']
      }

      mockFs.existsSync
        .mockReturnValueOnce(true) // metadata exists
        .mockReturnValueOnce(false) // project directory doesn't exist

      mockFs.readFileSync.mockReturnValue(JSON.stringify(mockMetadata))

      const request = new NextRequest('http://localhost/api/projects/test-project')
      const response = await GET(request, { params: { id: 'test-project' } })
      const data = await response.json()

      expect(response.status).toBe(200)
      expect(data.files).toEqual([])
      expect(data.file_structure).toBeNull()
      expect(data.stats.total_files).toBe(0)
    })

    it('should calculate correct project stats', async () => {
      const mockMetadata = {
        name: 'Test Project',
        status: 'active',
        tags: ['web-app']
      }

      const mockFiles = [
        'index.ts',
        'components/Header.tsx',
        'utils/helpers.ts',
        'README.md',
        'package.json'
      ]

      mockFs.existsSync.mockReturnValue(true)
      mockFs.readFileSync.mockReturnValue(JSON.stringify(mockMetadata))
      
      // Mock recursive file reading
      const walkSync = jest.fn().mockReturnValue(mockFiles)
      global.walkSync = walkSync

      mockFs.readdirSync.mockReturnValue([])
      mockFs.statSync
        .mockReturnValueOnce({ isDirectory: () => false, size: 500 } as any) // index.ts
        .mockReturnValueOnce({ isDirectory: () => false, size: 1200 } as any) // Header.tsx
        .mockReturnValueOnce({ isDirectory: () => false, size: 300 } as any) // helpers.ts
        .mockReturnValueOnce({ isDirectory: () => false, size: 800 } as any) // README.md
        .mockReturnValueOnce({ isDirectory: () => false, size: 400 } as any) // package.json

      const request = new NextRequest('http://localhost/api/projects/test-project')
      const response = await GET(request, { params: { id: 'test-project' } })
      const data = await response.json()

      expect(response.status).toBe(200)
      expect(data.stats.total_files).toBe(5)
      expect(data.stats.ts_files).toBe(2)
      expect(data.stats.tsx_files).toBe(1)
      expect(data.stats.total_size).toBeGreaterThan(0)
    })

    it('should handle file system errors gracefully', async () => {
      mockFs.existsSync
        .mockReturnValueOnce(true) // metadata exists
        .mockReturnValueOnce(true) // project directory exists

      mockFs.readFileSync.mockImplementation(() => {
        throw new Error('Permission denied')
      })

      const request = new NextRequest('http://localhost/api/projects/test-project')
      const response = await GET(request, { params: { id: 'test-project' } })
      const data = await response.json()

      expect(response.status).toBe(500)
      expect(data.error).toBe('Failed to get project details')
    })
  })
})