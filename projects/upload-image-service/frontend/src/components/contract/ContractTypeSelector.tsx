import React from 'react';
import { ContractType } from '../../types/contract';
import './ContractTypeSelector.css';

interface ContractTypeSelectorProps {
  onSelect: (type: ContractType) => void;
}

export const ContractTypeSelector: React.FC<ContractTypeSelectorProps> = ({ onSelect }) => {
  return (
    <div className="contract-type-selector">
      <h2>契約タイプを選択してください</h2>
      <div className="type-cards">
        <div 
          className="type-card individual"
          onClick={() => onSelect(ContractType.INDIVIDUAL)}
        >
          <div className="type-icon">👤</div>
          <h3>個人契約者用</h3>
          <ul className="document-list">
            <li>申込書一式（PDF）</li>
            <li>住民票（3か月以内）</li>
            <li>印鑑登録証明書（3か月以内）</li>
            <li>確定申告書</li>
            <li>運転免許証（両面）</li>
            <li>通帳コピー</li>
          </ul>
          <button className="select-button">個人契約で進む</button>
        </div>

        <div 
          className="type-card corporate"
          onClick={() => onSelect(ContractType.CORPORATE)}
        >
          <div className="type-icon">🏢</div>
          <h3>法人契約者用</h3>
          <div className="document-sections">
            <div className="section">
              <h4>法人書類</h4>
              <ul className="document-list">
                <li>申込書一式（PDF）</li>
                <li>履歴事項全部証明書</li>
                <li>印鑑証明書</li>
                <li>決算報告書一式</li>
              </ul>
            </div>
            <div className="section">
              <h4>代表者書類</h4>
              <ul className="document-list">
                <li>住民票</li>
                <li>印鑑登録証明書</li>
                <li>確定申告書</li>
                <li>運転免許証</li>
              </ul>
            </div>
          </div>
          <button className="select-button">法人契約で進む</button>
        </div>
      </div>
    </div>
  );
};