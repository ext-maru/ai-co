import { NextRequest } from 'next/server'
import { GET } from '@/app/api/projects/stats/route'
import fs from 'fs'
import path from 'path'

jest.mock('fs')
jest.mock('path')

const mockFs = fs as jest.Mocked<typeof fs>
const mockPath = path as jest.Mocked<typeof path>

describe('/api/projects/stats', () => {
  beforeEach(() => {
    jest.clearAllMocks()
    mockPath.resolve.mockImplementation((...args) => args.join('/'))
    mockPath.join.mockImplementation((...args) => args.join('/'))
  })

  it('should return empty stats when no projects exist', async () => {
    mockFs.existsSync.mockReturnValue(false)
    
    const request = new NextRequest('http://localhost/api/projects/stats')
    const response = await GET(request)
    const data = await response.json()

    expect(response.status).toBe(200)
    expect(data).toEqual({
      total_projects: 0,
      active_projects: 0,
      completed_projects: 0,
      planning_projects: 0,
      projects_by_type: {
        application: 0,
        library: 0,
        script: 0,
        other: 0
      },
      projects_by_status: {
        planning: 0,
        development: 0,
        testing: 0,
        active: 0,
        completed: 0,
        maintenance: 0
      },
      recent_projects: [],
      tech_stack_usage: {}
    })
  })

  it('should calculate correct stats for multiple projects', async () => {
    const mockProjects = ['project-1.json', 'project-2.json', 'project-3.json']
    
    const mockMetadata = [
      {
        name: 'Project 1',
        status: 'active',
        tags: ['web-app'],
        dependencies: ['react', 'typescript'],
        actual_completion: '2024-01-15'
      },
      {
        name: 'Project 2',
        status: 'completed',
        tags: ['script'],
        dependencies: ['python', 'numpy'],
        actual_completion: '2024-01-10'
      },
      {
        name: 'Project 3',
        status: 'planning',
        tags: ['library'],
        dependencies: ['typescript'],
        estimated_completion: '2024-02-01'
      }
    ]

    mockFs.existsSync.mockReturnValue(true)
    mockFs.readdirSync.mockReturnValue(mockProjects as any)
    mockFs.readFileSync
      .mockReturnValueOnce(JSON.stringify(mockMetadata[0]))
      .mockReturnValueOnce(JSON.stringify(mockMetadata[1]))
      .mockReturnValueOnce(JSON.stringify(mockMetadata[2]))

    const request = new NextRequest('http://localhost/api/projects/stats')
    const response = await GET(request)
    const data = await response.json()

    expect(response.status).toBe(200)
    expect(data.total_projects).toBe(3)
    expect(data.active_projects).toBe(1)
    expect(data.completed_projects).toBe(1)
    expect(data.planning_projects).toBe(1)
    expect(data.projects_by_type.application).toBe(1)
    expect(data.projects_by_type.script).toBe(1)
    expect(data.projects_by_type.library).toBe(1)
    expect(data.tech_stack_usage.typescript).toBe(2)
    expect(data.tech_stack_usage.react).toBe(1)
    expect(data.tech_stack_usage.python).toBe(1)
    expect(data.recent_projects).toHaveLength(3)
    expect(data.recent_projects[0].name).toBe('Project 1') // Most recent
  })

  it('should handle file read errors gracefully', async () => {
    mockFs.existsSync.mockReturnValue(true)
    mockFs.readdirSync.mockReturnValue(['error-project.json'] as any)
    mockFs.readFileSync.mockImplementation(() => {
      throw new Error('File read error')
    })

    const request = new NextRequest('http://localhost/api/projects/stats')
    const response = await GET(request)
    const data = await response.json()

    expect(response.status).toBe(200)
    expect(data.total_projects).toBe(0)
    expect(data.recent_projects).toEqual([])
  })

  it('should limit recent projects to 5', async () => {
    const mockProjects = Array(10).fill(null).map((_, i) => `project-${i}.json`)
    
    mockFs.existsSync.mockReturnValue(true)
    mockFs.readdirSync.mockReturnValue(mockProjects as any)
    
    // Mock 10 projects
    for (let i = 0; i < 10; i++) {
      mockFs.readFileSync.mockReturnValueOnce(JSON.stringify({
        name: `Project ${i}`,
        status: 'active',
        tags: ['web-app'],
        dependencies: [],
        actual_completion: new Date(2024, 0, i + 1).toISOString()
      }))
    }

    const request = new NextRequest('http://localhost/api/projects/stats')
    const response = await GET(request)
    const data = await response.json()

    expect(response.status).toBe(200)
    expect(data.total_projects).toBe(10)
    expect(data.recent_projects).toHaveLength(5)
  })

  it('should handle various project types correctly', async () => {
    const mockProjects = ['project-1.json']
    
    const mockMetadata = {
      name: 'Test Project',
      status: 'active',
      tags: ['monitoring', 'dashboard'], // Should be categorized as 'application'
      dependencies: []
    }

    mockFs.existsSync.mockReturnValue(true)
    mockFs.readdirSync.mockReturnValue(mockProjects as any)
    mockFs.readFileSync.mockReturnValue(JSON.stringify(mockMetadata))

    const request = new NextRequest('http://localhost/api/projects/stats')
    const response = await GET(request)
    const data = await response.json()

    expect(data.projects_by_type.application).toBe(1)
  })
})