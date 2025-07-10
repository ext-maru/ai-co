import { NextRequest } from 'next/server'
import { GET, POST, PATCH, DELETE } from '@/app/api/projects/[id]/notes/route'
import fs from 'fs'
import path from 'path'

// Mock uuid
jest.mock('uuid', () => ({
  v4: jest.fn(() => 'mock-uuid-123')
}))

jest.mock('fs')
jest.mock('path')

const mockFs = fs as jest.Mocked<typeof fs>
const mockPath = path as jest.Mocked<typeof path>

describe('/api/projects/[id]/notes', () => {
  beforeEach(() => {
    jest.clearAllMocks()
    mockPath.resolve.mockImplementation((...args) => args.join('/'))
    mockPath.join.mockImplementation((...args) => args.join('/'))
  })

  const mockNotes = [
    {
      id: 'note-1',
      project_id: 'test-project',
      author: 'Alice',
      content: 'First note',
      created_at: '2024-01-01T10:00:00Z',
      updated_at: '2024-01-01T10:00:00Z',
      tags: ['important']
    },
    {
      id: 'note-2',
      project_id: 'test-project',
      author: 'Bob',
      content: 'Second note',
      created_at: '2024-01-02T10:00:00Z',
      updated_at: '2024-01-02T10:00:00Z',
      tags: []
    }
  ]

  describe('GET', () => {
    it('should return all notes for a project sorted by date', async () => {
      mockFs.existsSync.mockReturnValue(true)
      mockFs.readFileSync.mockReturnValue(JSON.stringify(mockNotes))

      const request = new NextRequest('http://localhost/api/projects/test-project/notes')
      const response = await GET(request, { params: { id: 'test-project' } })
      const data = await response.json()

      expect(response.status).toBe(200)
      expect(data.project_id).toBe('test-project')
      expect(data.total_notes).toBe(2)
      expect(data.notes).toHaveLength(2)
      expect(data.notes[0].id).toBe('note-2') // Most recent first
    })

    it('should return empty array when no notes exist', async () => {
      mockFs.existsSync.mockReturnValue(false)

      const request = new NextRequest('http://localhost/api/projects/test-project/notes')
      const response = await GET(request, { params: { id: 'test-project' } })
      const data = await response.json()

      expect(response.status).toBe(200)
      expect(data.notes).toEqual([])
      expect(data.total_notes).toBe(0)
    })

    it('should handle file read errors', async () => {
      mockFs.existsSync.mockReturnValue(true)
      mockFs.readFileSync.mockImplementation(() => {
        throw new Error('Permission denied')
      })

      const request = new NextRequest('http://localhost/api/projects/test-project/notes')
      const response = await GET(request, { params: { id: 'test-project' } })
      const data = await response.json()

      expect(response.status).toBe(500)
      expect(data.error).toBe('Failed to get notes')
    })
  })

  describe('POST', () => {
    it('should create a new note successfully', async () => {
      mockFs.existsSync.mockReturnValue(true)
      mockFs.readFileSync.mockReturnValue(JSON.stringify([]))
      mockFs.writeFileSync.mockImplementation(() => {})

      const newNote = {
        author: 'Charlie',
        content: 'New note content',
        tags: ['review', 'urgent']
      }

      const request = new NextRequest('http://localhost/api/projects/test-project/notes', {
        method: 'POST',
        body: JSON.stringify(newNote)
      })
      
      const response = await POST(request, { params: { id: 'test-project' } })
      const data = await response.json()

      expect(response.status).toBe(201)
      expect(data.success).toBe(true)
      expect(data.note.id).toBe('mock-uuid-123')
      expect(data.note.author).toBe(newNote.author)
      expect(data.note.content).toBe(newNote.content)
      expect(data.note.tags).toEqual(newNote.tags)
      expect(data.note.created_at).toBeDefined()
    })

    it('should reject note creation without required fields', async () => {
      const invalidNote = {
        content: 'Missing author'
        // Missing author
      }

      const request = new NextRequest('http://localhost/api/projects/test-project/notes', {
        method: 'POST',
        body: JSON.stringify(invalidNote)
      })
      
      const response = await POST(request, { params: { id: 'test-project' } })
      const data = await response.json()

      expect(response.status).toBe(400)
      expect(data.error).toBe('content and author are required')
    })

    it('should create directory if it does not exist', async () => {
      mockFs.existsSync.mockReturnValue(false)
      mockFs.mkdirSync.mockImplementation(() => {})
      mockFs.writeFileSync.mockImplementation(() => {})

      const newNote = {
        author: 'Charlie',
        content: 'New note'
      }

      const request = new NextRequest('http://localhost/api/projects/test-project/notes', {
        method: 'POST',
        body: JSON.stringify(newNote)
      })
      
      const response = await POST(request, { params: { id: 'test-project' } })

      expect(response.status).toBe(201)
      expect(mockFs.mkdirSync).toHaveBeenCalled()
    })
  })

  describe('PATCH', () => {
    it('should update note content successfully', async () => {
      mockFs.existsSync.mockReturnValue(true)
      mockFs.readFileSync.mockReturnValue(JSON.stringify(mockNotes))
      mockFs.writeFileSync.mockImplementation(() => {})

      const updateData = {
        note_id: 'note-1',
        content: 'Updated content',
        tags: ['updated', 'important']
      }

      const request = new NextRequest('http://localhost/api/projects/test-project/notes', {
        method: 'PATCH',
        body: JSON.stringify(updateData)
      })
      
      const response = await PATCH(request, { params: { id: 'test-project' } })
      const data = await response.json()

      expect(response.status).toBe(200)
      expect(data.success).toBe(true)
      expect(data.note.content).toBe(updateData.content)
      expect(data.note.tags).toEqual(updateData.tags)
      expect(data.note.updated_at).not.toBe(mockNotes[0].updated_at)
    })

    it('should reject update without note_id', async () => {
      const updateData = {
        content: 'Updated content'
        // Missing note_id
      }

      const request = new NextRequest('http://localhost/api/projects/test-project/notes', {
        method: 'PATCH',
        body: JSON.stringify(updateData)
      })
      
      const response = await PATCH(request, { params: { id: 'test-project' } })
      const data = await response.json()

      expect(response.status).toBe(400)
      expect(data.error).toBe('note_id is required')
    })

    it('should return 404 for non-existent note', async () => {
      mockFs.existsSync.mockReturnValue(true)
      mockFs.readFileSync.mockReturnValue(JSON.stringify(mockNotes))

      const updateData = {
        note_id: 'non-existent',
        content: 'Updated content'
      }

      const request = new NextRequest('http://localhost/api/projects/test-project/notes', {
        method: 'PATCH',
        body: JSON.stringify(updateData)
      })
      
      const response = await PATCH(request, { params: { id: 'test-project' } })
      const data = await response.json()

      expect(response.status).toBe(404)
      expect(data.error).toBe('Note not found')
    })

    it('should only update provided fields', async () => {
      mockFs.existsSync.mockReturnValue(true)
      mockFs.readFileSync.mockReturnValue(JSON.stringify(mockNotes))
      mockFs.writeFileSync.mockImplementation(() => {})

      const updateData = {
        note_id: 'note-1',
        content: 'Only update content'
        // tags not provided, should remain unchanged
      }

      const request = new NextRequest('http://localhost/api/projects/test-project/notes', {
        method: 'PATCH',
        body: JSON.stringify(updateData)
      })
      
      const response = await PATCH(request, { params: { id: 'test-project' } })
      const data = await response.json()

      expect(response.status).toBe(200)
      expect(data.note.content).toBe(updateData.content)
      expect(data.note.tags).toEqual(mockNotes[0].tags) // Should remain unchanged
    })
  })

  describe('DELETE', () => {
    it('should delete note successfully', async () => {
      mockFs.existsSync.mockReturnValue(true)
      mockFs.readFileSync.mockReturnValue(JSON.stringify(mockNotes))
      mockFs.writeFileSync.mockImplementation(() => {})

      const request = new NextRequest('http://localhost/api/projects/test-project/notes?note_id=note-1')
      const response = await DELETE(request, { params: { id: 'test-project' } })
      const data = await response.json()

      expect(response.status).toBe(200)
      expect(data.success).toBe(true)
      expect(data.message).toBe('Note deleted successfully')
      
      // Verify the note was removed
      const writeCall = mockFs.writeFileSync.mock.calls[0]
      const writtenData = JSON.parse(writeCall[1] as string)
      expect(writtenData).toHaveLength(1)
      expect(writtenData[0].id).toBe('note-2')
    })

    it('should reject deletion without note_id', async () => {
      const request = new NextRequest('http://localhost/api/projects/test-project/notes')
      const response = await DELETE(request, { params: { id: 'test-project' } })
      const data = await response.json()

      expect(response.status).toBe(400)
      expect(data.error).toBe('note_id is required')
    })

    it('should return 404 for non-existent note', async () => {
      mockFs.existsSync.mockReturnValue(true)
      mockFs.readFileSync.mockReturnValue(JSON.stringify(mockNotes))

      const request = new NextRequest('http://localhost/api/projects/test-project/notes?note_id=non-existent')
      const response = await DELETE(request, { params: { id: 'test-project' } })
      const data = await response.json()

      expect(response.status).toBe(404)
      expect(data.error).toBe('Note not found')
    })
  })
})