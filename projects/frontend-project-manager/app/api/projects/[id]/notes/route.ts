import { NextRequest, NextResponse } from 'next/server'
import fs from 'fs'
import path from 'path'
import { v4 as uuidv4 } from 'uuid'

interface Note {
  id: string
  project_id: string
  author: string
  content: string
  created_at: string
  updated_at: string
  tags?: string[]
}

// ノートファイルのパスを取得
function getNotesFilePath(projectId: string): string {
  const notesDir = path.resolve(process.cwd(), '../../data/project_notes')
  if (!fs.existsSync(notesDir)) {
    fs.mkdirSync(notesDir, { recursive: true })
  }
  return path.join(notesDir, `${projectId}.json`)
}

// ノートを読み込む
function loadNotes(projectId: string): Note[] {
  const filePath = getNotesFilePath(projectId)

  if (!fs.existsSync(filePath)) {
    return []
  }

  try {
    const data = fs.readFileSync(filePath, 'utf8')
    return JSON.parse(data)
  } catch (error) {
    console.error('Error loading notes:', error)
    return []
  }
}

// ノートを保存
function saveNotes(projectId: string, notes: Note[]): void {
  const filePath = getNotesFilePath(projectId)
  fs.writeFileSync(filePath, JSON.stringify(notes, null, 2))
}

// ノート一覧取得
export async function GET(
  request: NextRequest,
  { params }: { params: { id: string } }
) {
  try {
    console.log('Getting notes for project:', params.id)

    const notes = loadNotes(params.id)

    // 新しい順にソート
    notes.sort((a, b) =>
      new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
    )

    return NextResponse.json({
      project_id: params.id,
      total_notes: notes.length,
      notes
    })

  } catch (error) {
    console.error('Get notes error:', error)
    return NextResponse.json(
      { error: 'Failed to get notes' },
      { status: 500 }
    )
  }
}

// 新規ノート作成
export async function POST(
  request: NextRequest,
  { params }: { params: { id: string } }
) {
  try {
    const body = await request.json()
    console.log('Creating note for project:', params.id)

    // 必須フィールドの検証
    if (!body.content || !body.author) {
      return NextResponse.json(
        { error: 'content and author are required' },
        { status: 400 }
      )
    }

    const notes = loadNotes(params.id)

    // 新規ノート作成
    const newNote: Note = {
      id: uuidv4(),
      project_id: params.id,
      author: body.author,
      content: body.content,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
      tags: body.tags || []
    }

    notes.push(newNote)
    saveNotes(params.id, notes)

    console.log('Note created successfully:', newNote.id)
    return NextResponse.json({
      success: true,
      note: newNote
    }, { status: 201 })

  } catch (error) {
    console.error('Create note error:', error)
    return NextResponse.json(
      { error: 'Failed to create note' },
      { status: 500 }
    )
  }
}

// ノート更新
export async function PATCH(
  request: NextRequest,
  { params }: { params: { id: string } }
) {
  try {
    const body = await request.json()
    const noteId = body.note_id

    if (!noteId) {
      return NextResponse.json(
        { error: 'note_id is required' },
        { status: 400 }
      )
    }

    console.log('Updating note:', noteId, 'for project:', params.id)

    const notes = loadNotes(params.id)
    const noteIndex = notes.findIndex(n => n.id === noteId)

    if (noteIndex === -1) {
      return NextResponse.json(
        { error: 'Note not found' },
        { status: 404 }
      )
    }

    // 更新可能なフィールドのみ更新
    if (body.content !== undefined) {
      notes[noteIndex].content = body.content
    }

    if (body.tags !== undefined) {
      notes[noteIndex].tags = body.tags
    }

    notes[noteIndex].updated_at = new Date().toISOString()

    saveNotes(params.id, notes)

    console.log('Note updated successfully:', noteId)
    return NextResponse.json({
      success: true,
      note: notes[noteIndex]
    })

  } catch (error) {
    console.error('Update note error:', error)
    return NextResponse.json(
      { error: 'Failed to update note' },
      { status: 500 }
    )
  }
}

// ノート削除
export async function DELETE(
  request: NextRequest,
  { params }: { params: { id: string } }
) {
  try {
    const url = new URL(request.url)
    const noteId = url.searchParams.get('note_id')

    if (!noteId) {
      return NextResponse.json(
        { error: 'note_id is required' },
        { status: 400 }
      )
    }

    console.log('Deleting note:', noteId, 'for project:', params.id)

    const notes = loadNotes(params.id)
    const filteredNotes = notes.filter(n => n.id !== noteId)

    if (filteredNotes.length === notes.length) {
      return NextResponse.json(
        { error: 'Note not found' },
        { status: 404 }
      )
    }

    saveNotes(params.id, filteredNotes)

    console.log('Note deleted successfully:', noteId)
    return NextResponse.json({
      success: true,
      message: 'Note deleted successfully'
    })

  } catch (error) {
    console.error('Delete note error:', error)
    return NextResponse.json(
      { error: 'Failed to delete note' },
      { status: 500 }
    )
  }
}
