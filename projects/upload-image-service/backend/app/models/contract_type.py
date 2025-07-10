from enum import Enum
from typing import Dict
from typing import List

from pydantic import BaseModel


class ContractType(str, Enum):
    """契約タイプ"""

    INDIVIDUAL = "individual"  # 個人契約者
    CORPORATE = "corporate"  # 法人契約者


class DocumentType(str, Enum):
    """書類タイプ"""

    # 個人契約者用
    RESIDENT_CARD = "resident_card"  # 住民票
    SEAL_CERTIFICATE = "seal_certificate"  # 印鑑登録証明書
    TAX_RETURN = "tax_return"  # 確定申告書
    DRIVERS_LICENSE = "drivers_license"  # 運転免許証
    BANK_BOOK = "bank_book"  # 通帳コピー

    # 法人契約者用
    CORPORATE_REGISTRY = "corporate_registry"  # 履歴事項全部証明書
    CORPORATE_SEAL_CERT = "corporate_seal_cert"  # 法人印鑑証明書
    FINANCIAL_STATEMENT = "financial_statement"  # 決算報告書
    BALANCE_SHEET = "balance_sheet"  # 貸借対照表
    INCOME_STATEMENT = "income_statement"  # 損益計算書
    EQUITY_STATEMENT = "equity_statement"  # 株主資本等変動計算書

    # 代表者用（法人の場合）
    REP_RESIDENT_CARD = "rep_resident_card"  # 代表者住民票
    REP_SEAL_CERTIFICATE = "rep_seal_certificate"  # 代表者印鑑登録証明書
    REP_TAX_RETURN = "rep_tax_return"  # 代表者確定申告書
    REP_DRIVERS_LICENSE = "rep_drivers_license"  # 代表者運転免許証


class DocumentRequirement(BaseModel):
    """書類要件定義"""

    document_type: DocumentType
    display_name: str
    description: str
    required: bool = True
    max_files: int = 1
    allowed_formats: List[str] = [".pdf", ".jpg", ".jpeg", ".png"]
    max_size_mb: int = 10
    expiry_days: int = 0  # 0は期限なし、例：住民票は90日


# 書類要件定義
DOCUMENT_REQUIREMENTS: Dict[ContractType, List[DocumentRequirement]] = {
    ContractType.INDIVIDUAL: [
        DocumentRequirement(
            document_type=DocumentType.RESIDENT_CARD,
            display_name="住民票",
            description="発行から3か月以内のもの",
            expiry_days=90,
        ),
        DocumentRequirement(
            document_type=DocumentType.SEAL_CERTIFICATE,
            display_name="印鑑登録証明書",
            description="発行から3か月以内のもの",
            expiry_days=90,
        ),
        DocumentRequirement(
            document_type=DocumentType.TAX_RETURN,
            display_name="直近1期分の確定申告書",
            description="最新の確定申告書を提出してください",
            max_size_mb=30,
        ),
        DocumentRequirement(
            document_type=DocumentType.DRIVERS_LICENSE,
            display_name="運転免許証",
            description="おもて・うらのコピー",
            max_files=2,
        ),
        DocumentRequirement(
            document_type=DocumentType.BANK_BOOK,
            display_name="取引口座の通帳コピー",
            description="おもて面・見開き1・2ページ目",
            max_files=3,
        ),
    ],
    ContractType.CORPORATE: [
        # 法人本体の書類
        DocumentRequirement(
            document_type=DocumentType.CORPORATE_REGISTRY,
            display_name="履歴事項全部証明書",
            description="法人の履歴事項全部証明書",
            expiry_days=90,
        ),
        DocumentRequirement(
            document_type=DocumentType.CORPORATE_SEAL_CERT,
            display_name="印鑑証明書",
            description="法人の印鑑証明書",
            expiry_days=90,
        ),
        DocumentRequirement(
            document_type=DocumentType.FINANCIAL_STATEMENT,
            display_name="直近1期分の決算報告書",
            description="以下3点を含む決算報告書",
            max_files=4,
            max_size_mb=50,
        ),
        DocumentRequirement(
            document_type=DocumentType.BALANCE_SHEET,
            display_name="貸借対照表",
            description="決算報告書に含まれる貸借対照表",
            max_size_mb=20,
        ),
        DocumentRequirement(
            document_type=DocumentType.INCOME_STATEMENT,
            display_name="損益計算書",
            description="決算報告書に含まれる損益計算書",
            max_size_mb=20,
        ),
        DocumentRequirement(
            document_type=DocumentType.EQUITY_STATEMENT,
            display_name="株主資本等変動計算書",
            description="決算報告書に含まれる株主資本等変動計算書",
            max_size_mb=20,
        ),
        # 代表者の書類
        DocumentRequirement(
            document_type=DocumentType.REP_RESIDENT_CARD,
            display_name="代表者の住民票",
            description="代表者個人の住民票（発行から3か月以内）",
            expiry_days=90,
        ),
        DocumentRequirement(
            document_type=DocumentType.REP_SEAL_CERTIFICATE,
            display_name="代表者の印鑑登録証明書",
            description="代表者個人の印鑑登録証明書（発行から3か月以内）",
            expiry_days=90,
        ),
        DocumentRequirement(
            document_type=DocumentType.REP_TAX_RETURN,
            display_name="代表者の直近の確定申告書",
            description="代表者個人の最新の確定申告書",
            max_size_mb=30,
        ),
        DocumentRequirement(
            document_type=DocumentType.REP_DRIVERS_LICENSE,
            display_name="代表者の運転免許証",
            description="代表者の運転免許証（おもて・うらのコピー）",
            max_files=2,
        ),
    ],
}


class DocumentCategory(BaseModel):
    """書類カテゴリ"""

    name: str
    documents: List[DocumentRequirement]


def get_document_categories(contract_type: ContractType) -> List[DocumentCategory]:
    """契約タイプに応じた書類カテゴリを取得"""
    requirements = DOCUMENT_REQUIREMENTS[contract_type]

    if contract_type == ContractType.INDIVIDUAL:
        return [DocumentCategory(name="必要書類", documents=requirements)]
    else:  # CORPORATE
        # 法人書類と代表者書類を分ける
        corporate_docs = [req for req in requirements if not req.document_type.value.startswith("rep_")]
        representative_docs = [req for req in requirements if req.document_type.value.startswith("rep_")]

        return [
            DocumentCategory(name="法人本体の書類", documents=corporate_docs),
            DocumentCategory(name="代表者の書類", documents=representative_docs),
        ]
