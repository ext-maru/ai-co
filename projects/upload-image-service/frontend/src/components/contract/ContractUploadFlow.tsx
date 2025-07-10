import React, { useState, useEffect } from 'react';
import { ContractTypeSelector } from './ContractTypeSelector';
import { DocumentUploadPanel } from './DocumentUploadPanel';
import { ContractType, ContractUploadDetail, ContractRequirementsResponse } from '../../types/contract';
import { getContractRequirements, createContractUpload, getContractUploadDetail } from '../../services/contractApi';
import './ContractUploadFlow.css';

interface ContractUploadFlowProps {
  onComplete?: (contractUploadId: string) => void;
}

enum FlowStep {
  TYPE_SELECTION = 'type_selection',
  DOCUMENT_UPLOAD = 'document_upload',
  COMPLETION = 'completion'
}

export const ContractUploadFlow: React.FC<ContractUploadFlowProps> = ({ onComplete }) => {
  const [currentStep, setCurrentStep] = useState<FlowStep>(FlowStep.TYPE_SELECTION);
  const [contractType, setContractType] = useState<ContractType | null>(null);
  const [requirements, setRequirements] = useState<ContractRequirementsResponse | null>(null);
  const [contractUploadId, setContractUploadId] = useState<string | null>(null);
  const [contractDetail, setContractDetail] = useState<ContractUploadDetail | null>(null);
  const [loading, setLoading] = useState(false);

  // 契約タイプ選択時の処理
  const handleTypeSelection = async (selectedType: ContractType) => {
    setLoading(true);
    try {
      // 契約要件取得
      const reqs = await getContractRequirements(selectedType);
      setRequirements(reqs);
      
      // 契約アップロードセッション作成
      const contractUpload = await createContractUpload({
        contract_type: selectedType,
        metadata: {}
      });
      
      setContractType(selectedType);
      setContractUploadId(contractUpload.id);
      setCurrentStep(FlowStep.DOCUMENT_UPLOAD);
      
    } catch (error) {
      console.error('Failed to initialize contract upload:', error);
      alert('契約タイプの設定に失敗しました。もう一度お試しください。');
    } finally {
      setLoading(false);
    }
  };

  // 書類アップロード完了時の処理
  const handleUploadComplete = () => {
    if (contractUploadId) {
      loadContractDetail();
    }
  };

  // 契約詳細読み込み
  const loadContractDetail = async () => {
    if (!contractUploadId) return;
    
    try {
      const detail = await getContractUploadDetail(contractUploadId);
      setContractDetail(detail);
      
      // 完了率100%なら次のステップへ
      if (detail.completion_rate >= 100) {
        setCurrentStep(FlowStep.COMPLETION);
        if (onComplete) {
          onComplete(contractUploadId);
        }
      }
    } catch (error) {
      console.error('Failed to load contract detail:', error);
    }
  };

  // ステップ表示名
  const getStepDisplayName = (step: FlowStep): string => {
    switch (step) {
      case FlowStep.TYPE_SELECTION:
        return '契約タイプ選択';
      case FlowStep.DOCUMENT_UPLOAD:
        return '書類アップロード';
      case FlowStep.COMPLETION:
        return '完了';
      default:
        return '';
    }
  };

  // プログレスバーの計算
  const getProgressPercent = (): number => {
    switch (currentStep) {
      case FlowStep.TYPE_SELECTION:
        return 33;
      case FlowStep.DOCUMENT_UPLOAD:
        return contractDetail ? 33 + (contractDetail.completion_rate * 0.67) : 33;
      case FlowStep.COMPLETION:
        return 100;
      default:
        return 0;
    }
  };

  return (
    <div className="contract-upload-flow">
      {/* プログレスヘッダー */}
      <div className="flow-header">
        <h1>契約書類アップロード</h1>
        <div className="progress-section">
          <div className="progress-bar">
            <div 
              className="progress-fill" 
              style={{ width: `${getProgressPercent()}%` }}
            />
          </div>
          <div className="step-indicators">
            <div className={`step ${currentStep === FlowStep.TYPE_SELECTION ? 'active' : 'completed'}`}>
              <span className="step-number">1</span>
              <span className="step-label">契約タイプ選択</span>
            </div>
            <div className={`step ${currentStep === FlowStep.DOCUMENT_UPLOAD ? 'active' : currentStep === FlowStep.COMPLETION ? 'completed' : ''}`}>
              <span className="step-number">2</span>
              <span className="step-label">書類アップロード</span>
            </div>
            <div className={`step ${currentStep === FlowStep.COMPLETION ? 'active' : ''}`}>
              <span className="step-number">3</span>
              <span className="step-label">完了</span>
            </div>
          </div>
        </div>
      </div>

      {/* コンテンツエリア */}
      <div className="flow-content">
        {loading && (
          <div className="loading-overlay">
            <div className="spinner"></div>
            <p>処理中...</p>
          </div>
        )}

        {currentStep === FlowStep.TYPE_SELECTION && (
          <ContractTypeSelector onSelect={handleTypeSelection} />
        )}

        {currentStep === FlowStep.DOCUMENT_UPLOAD && requirements && contractUploadId && (
          <DocumentUploadPanel
            contractType={contractType!}
            requirements={requirements}
            contractUploadId={contractUploadId}
            onUploadComplete={handleUploadComplete}
            contractDetail={contractDetail}
          />
        )}

        {currentStep === FlowStep.COMPLETION && contractDetail && (
          <div className="completion-screen">
            <div className="completion-icon">✅</div>
            <h2>書類アップロード完了</h2>
            <p>すべての必要書類のアップロードが完了しました。</p>
            
            <div className="completion-summary">
              <h3>アップロード情報</h3>
              <ul>
                <li>契約タイプ: {contractType === ContractType.INDIVIDUAL ? '個人契約者' : '法人契約者'}</li>
                <li>完了率: {contractDetail.completion_rate}%</li>
                <li>アップロード書類数: {contractDetail.document_statuses.filter(d => d.uploaded).length}件</li>
              </ul>
            </div>

            <div className="next-steps">
              <h3>次のステップ</h3>
              <ol>
                <li>管理者による書類審査が開始されます</li>
                <li>審査結果はメールでお知らせします</li>
                <li>追加書類が必要な場合は、再度アップロードをお願いする場合があります</li>
              </ol>
            </div>

            <div className="action-buttons">
              <button 
                className="btn-primary"
                onClick={() => window.location.href = '/dashboard'}
              >
                ダッシュボードに戻る
              </button>
              <button 
                className="btn-secondary"
                onClick={() => {
                  setCurrentStep(FlowStep.TYPE_SELECTION);
                  setContractType(null);
                  setRequirements(null);
                  setContractUploadId(null);
                  setContractDetail(null);
                }}
              >
                新しい契約を開始
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};