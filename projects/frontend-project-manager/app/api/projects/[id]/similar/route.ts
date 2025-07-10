import { NextRequest, NextResponse } from 'next/server'
import fs from 'fs'
import path from 'path'

interface SimilarProject {
  project_id: string
  name: string
  description: string
  similarity: number
  tech_stack: string[]
  status: string
  similarity_reasons: string[]
}

// 類似プロジェクトを検索
async function findSimilarProjects(projectId: string): Promise<SimilarProject[]> {
  try {
    // 対象プロジェクトのメタデータを読み込む
    const targetMetadataPath = path.resolve(process.cwd(), '../../data/project_metadata', `${projectId}.json`)
    
    if (!fs.existsSync(targetMetadataPath)) {
      return []
    }
    
    const targetMetadata = JSON.parse(fs.readFileSync(targetMetadataPath, 'utf8'))
    const targetTechStack = new Set(targetMetadata.dependencies || [])
    const targetTags = new Set(targetMetadata.tags || [])
    
    // すべてのプロジェクトメタデータを読み込む
    const metadataPath = path.resolve(process.cwd(), '../../data/project_metadata')
    const files = fs.readdirSync(metadataPath)
    
    const similarProjects: SimilarProject[] = []
    
    for (const file of files) {
      if (!file.endsWith('.json')) continue
      
      const currentProjectId = file.replace('.json', '')
      
      // 自分自身はスキップ
      if (currentProjectId === projectId) continue
      
      try {
        const filePath = path.join(metadataPath, file)
        const metadata = JSON.parse(fs.readFileSync(filePath, 'utf8'))
        
        // 類似度を計算
        const similarityData = calculateSimilarity(
          targetMetadata,
          metadata,
          targetTechStack,
          targetTags
        )
        
        if (similarityData.score > 0.2) { // 20%以上の類似度があれば含める
          similarProjects.push({
            project_id: currentProjectId,
            name: metadata.name,
            description: getDescription(currentProjectId, metadata),
            similarity: similarityData.score,
            tech_stack: metadata.dependencies || [],
            status: metadata.status,
            similarity_reasons: similarityData.reasons
          })
        }
      } catch (error) {
        console.error(`Error processing ${file}:`, error)
      }
    }
    
    // 類似度でソート（降順）
    similarProjects.sort((a, b) => b.similarity - a.similarity)
    
    // 上位5件を返す
    return similarProjects.slice(0, 5)
    
  } catch (error) {
    console.error('Error finding similar projects:', error)
    return []
  }
}

// 類似度計算
function calculateSimilarity(
  targetMetadata: any,
  comparisonMetadata: any,
  targetTechStack: Set<string>,
  targetTags: Set<string>
): { score: number; reasons: string[] } {
  let score = 0
  const reasons: string[] = []
  
  // 技術スタックの類似性（最大40%）
  const comparisonTechStack = new Set(comparisonMetadata.dependencies || [])
  const techIntersection = new Set([...targetTechStack].filter(x => comparisonTechStack.has(x)))
  
  if (techIntersection.size > 0) {
    const techScore = (techIntersection.size / Math.max(targetTechStack.size, comparisonTechStack.size)) * 0.4
    score += techScore
    
    const sharedTech = Array.from(techIntersection).join(', ')
    reasons.push(`共通技術: ${sharedTech}`)
  }
  
  // タグの類似性（最大30%）
  const comparisonTags = new Set(comparisonMetadata.tags || [])
  const tagIntersection = new Set([...targetTags].filter(x => comparisonTags.has(x)))
  
  if (tagIntersection.size > 0) {
    const tagScore = (tagIntersection.size / Math.max(targetTags.size, comparisonTags.size)) * 0.3
    score += tagScore
    
    const sharedTags = Array.from(tagIntersection).join(', ')
    reasons.push(`共通タグ: ${sharedTags}`)
  }
  
  // ステータスの類似性（最大10%）
  if (targetMetadata.status === comparisonMetadata.status) {
    score += 0.1
    reasons.push(`同じステータス: ${targetMetadata.status}`)
  }
  
  // プロジェクトタイプの類似性（最大20%）
  const targetType = getProjectType(targetMetadata.tags || [])
  const comparisonType = getProjectType(comparisonMetadata.tags || [])
  
  if (targetType === comparisonType) {
    score += 0.2
    reasons.push(`同じプロジェクトタイプ: ${targetType}`)
  }
  
  // 特定の技術組み合わせボーナス
  const targetHasWeb = hasWebTech(targetTechStack)
  const comparisonHasWeb = hasWebTech(comparisonTechStack)
  
  if (targetHasWeb && comparisonHasWeb) {
    score += 0.1
    reasons.push('両方ともWebアプリケーション')
  }
  
  return { score: Math.min(1, score), reasons }
}

// Web技術を持っているかチェック
function hasWebTech(techStack: Set<string>): boolean {
  const webTechs = ['next.js', 'react', 'vue', 'angular', 'flask', 'django', 'fastapi', 'express']
  return Array.from(techStack).some(tech => 
    webTechs.some(webTech => tech.toLowerCase().includes(webTech))
  )
}

// プロジェクトタイプを取得
function getProjectType(tags: string[]): string {
  if (tags.includes('web-app') || tags.includes('next.js')) return 'application'
  if (tags.includes('test-project') || tags.includes('tdd')) return 'script'
  if (tags.includes('monitoring') || tags.includes('dashboard')) return 'application'
  if (tags.includes('library')) return 'library'
  return 'application'
}

// プロジェクトの説明を取得
function getDescription(projectId: string, metadata: any): string {
  const descriptions: Record<string, string> = {
    'image-upload-manager': 'Google Drive統合による画像アップロード・顧客管理システム',
    'elders-guild-web': '4賢者リアルタイム通信システム',
    'frontend-project-manager': 'プロジェクト詳細表示・図表レンダリングシステム',
    'web-monitoring-dashboard': 'リアルタイム監視・分析ダッシュボード',
    'test-calculator-project': 'TDD学習・テスト実装の実習プロジェクト'
  }
  
  return descriptions[projectId] || metadata.description || 'プロジェクトの説明がありません'
}

export async function GET(
  request: NextRequest,
  { params }: { params: { id: string } }
) {
  try {
    console.log('Similar projects API called for:', params.id)
    
    const similarProjects = await findSimilarProjects(params.id)
    
    console.log(`Found ${similarProjects.length} similar projects for:`, params.id)
    return NextResponse.json(similarProjects)
    
  } catch (error) {
    console.error('Similar projects API error:', error)
    return NextResponse.json(
      { error: 'Internal Server Error' },
      { status: 500 }
    )
  }
}