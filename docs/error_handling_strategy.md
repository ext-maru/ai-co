# エラーハンドリング戦略 - Code Review System

## 🎯 エラーハンドリング方針

### 基本原則
1. **Fail Fast**: 早期にエラーを検出し、迅速に対応
2. **Graceful Degradation**: 部分的障害でもサービス継続
3. **Observability**: 全エラーを構造化ログで記録
4. **Recovery**: 可能な限り自動回復を試行

## 🔍 エラー分類

### レベル1: 回復可能エラー (Recoverable)
```python
class RecoverableError(Exception):
    """回復可能なエラー - リトライ対象"""
    def __init__(self, message: str, retry_after: int = 30):
        self.retry_after = retry_after
        super().__init__(message)

# 例:
- ネットワーク一時的エラー
- 外部API率制限エラー  
- メモリ不足エラー
- キュー満杯エラー
```

### レベル2: 部分的エラー (Partial)
```python
class PartialError(Exception):
    """部分的エラー - 一部機能は継続可能"""
    def __init__(self, message: str, failed_components: List[str]):
        self.failed_components = failed_components
        super().__init__(message)

# 例:
- 一部の解析機能エラー
- 特定言語のパーサーエラー
- 一部レポート形式生成エラー
```

### レベル3: 致命的エラー (Fatal)
```python
class FatalError(Exception):
    """致命的エラー - 処理中断必須"""
    def __init__(self, message: str, error_code: str):
        self.error_code = error_code
        super().__init__(message)

# 例:
- 不正なコード形式
- システムリソース枯渇
- 設定ファイル破損
- セキュリティ違反
```

## 🔄 ワーカー別エラーハンドリング

### TaskWorker エラーハンドリング
```python
class CodeReviewTaskWorker(AsyncTaskWorkerSimple):
    async def process_message(self, message: Dict[str, Any]) -> Dict[str, Any]:
        try:
            return await self._process_code_analysis(message)
        except RecoverableError as e:
            # リトライ可能エラー
            await self._schedule_retry(message, e.retry_after)
            raise
        except PartialError as e:
            # 部分的エラー - 可能な範囲で処理継続
            return await self._handle_partial_analysis(message, e)
        except FatalError as e:
            # 致命的エラー - 処理中断
            await self._log_fatal_error(message, e)
            return self._create_error_response(message, e)
        except Exception as e:
            # 予期しないエラー
            await self._handle_unexpected_error(message, e)
            raise FatalError(f"Unexpected error in TaskWorker: {str(e)}", "TASK_UNEXPECTED")
    
    async def _handle_partial_analysis(self, message: Dict, error: PartialError) -> Dict:
        """部分的エラーの処理 - 可能な解析のみ実行"""
        partial_results = {}
        
        # 構文解析のみ実行（他の解析が失敗した場合）
        if "syntax" not in error.failed_components:
            partial_results["syntax_issues"] = await self._analyze_syntax(message)
        
        # 部分結果でもPMWorkerに送信
        return {
            "status": "partial_success",
            "analysis_results": partial_results,
            "failed_components": error.failed_components,
            "error_message": str(error)
        }
```

### PMWorker エラーハンドリング
```python
class CodeReviewPMWorker(AsyncPMWorkerSimple):
    async def process_message(self, message: Dict[str, Any]) -> Dict[str, Any]:
        try:
            return await self._process_quality_evaluation(message)
        except RecoverableError as e:
            # TaskWorkerの再試行を待つ
            await asyncio.sleep(e.retry_after)
            return await self._request_task_retry(message)
        except PartialError as e:
            # 部分的結果でも品質評価実行
            return await self._evaluate_partial_results(message, e)
        except FatalError as e:
            # エラー結果としてResultWorkerに送信
            return await self._create_error_final_result(message, e)
    
    async def _evaluate_partial_results(self, message: Dict, error: PartialError) -> Dict:
        """部分的結果での品質評価"""
        # 利用可能なデータのみで品質スコア算出
        available_results = message.get("analysis_results", {})
        
        # 重み付けを調整して部分スコア算出
        partial_score = await self._calculate_partial_quality_score(available_results)
        
        # 部分結果でも改善提案生成
        if partial_score < 85:
            return await self._generate_improvement_for_partial(message, available_results)
        else:
            return await self._finalize_with_warnings(message, error.failed_components)
```

### ResultWorker エラーハンドリング
```python
class CodeReviewResultWorker(AsyncResultWorkerSimple):
    async def process_message(self, message: Dict[str, Any]) -> Dict[str, Any]:
        try:
            return await self._generate_final_report(message)
        except RecoverableError as e:
            # レポート生成リトライ
            await asyncio.sleep(e.retry_after)
            return await self._retry_report_generation(message)
        except PartialError as e:
            # 一部形式のみでレポート生成
            return await self._generate_partial_report(message, e)
        except FatalError as e:
            # エラーレポート生成
            return await self._generate_error_report(message, e)
    
    async def _generate_partial_report(self, message: Dict, error: PartialError) -> Dict:
        """部分的レポート生成 - 可能な形式のみ"""
        available_formats = set(["json", "markdown", "html"]) - set(error.failed_components)
        
        reports = {}
        for format_type in available_formats:
            try:
                reports[format_type] = await self._generate_format(message, format_type)
            except Exception as e:
                self.logger.warning(f"Failed to generate {format_type} report", error=str(e))
        
        return {
            "status": "partial_success",
            "generated_reports": reports,
            "failed_formats": error.failed_components,
            "warning": "Some report formats could not be generated"
        }
```

## 🔄 反復エラーハンドリング

### 反復制御エラー
```python
class IterationController:
    MAX_ITERATIONS = 5
    
    async def handle_iteration_errors(self, task_id: str, iteration: int, error: Exception):
        if iteration >= self.MAX_ITERATIONS:
            # 反復上限到達
            return await self._finalize_with_current_quality(task_id)
        
        if isinstance(error, RecoverableError):
            # 次の反復で再試行
            return await self._schedule_next_iteration(task_id, iteration + 1, error.retry_after)
        
        elif isinstance(error, PartialError):
            # 部分結果で次の反復実行
            return await self._continue_with_partial_results(task_id, iteration + 1, error)
        
        else:
            # 致命的エラー - 反復停止
            return await self._abort_iteration_cycle(task_id, error)
```

## 📊 エラー監視・アラート

### エラーメトリクス収集
```python
class ErrorMetricsCollector:
    def __init__(self, metrics_system):
        self.error_counter = metrics_system.counter('errors_total')
        self.error_histogram = metrics_system.histogram('error_processing_time')
        self.recovery_rate = metrics_system.gauge('error_recovery_rate')
    
    def record_error(self, error_type: str, component: str, recovery_success: bool):
        self.error_counter.labels(
            error_type=error_type,
            component=component,
            recovered=recovery_success
        ).inc()
        
        if recovery_success:
            self.recovery_rate.inc()
```

### アラート閾値
```yaml
alert_thresholds:
  error_rate:
    warning: "> 1% over 5 minutes"
    critical: "> 5% over 5 minutes"
  
  recovery_rate:
    warning: "< 90% over 10 minutes"
    critical: "< 70% over 10 minutes"
  
  fatal_errors:
    warning: "> 0 over 1 minute"
    critical: "> 3 over 5 minutes"
```

## 🧪 エラーハンドリングテスト

### エラー注入テスト
```python
class ErrorInjectionTests:
    async def test_network_failure_recovery(self):
        """ネットワーク障害からの回復テスト"""
        # Given: ネットワーク障害を注入
        with self.inject_network_failure():
            # When: コードレビュー実行
            result = await self.code_review_system.process(sample_code)
            # Then: 適切にリトライされ最終的に成功
        
    async def test_partial_component_failure(self):
        """部分的コンポーネント障害テスト"""
        # Given: セキュリティ解析コンポーネント障害
        with self.disable_component("security_analyzer"):
            # When: コードレビュー実行
            result = await self.code_review_system.process(sample_code)
            # Then: 他の解析は成功し、部分結果が返される
        
    async def test_iteration_cycle_error_handling(self):
        """反復サイクルエラーハンドリングテスト"""
        # Given: 3回目の反復で障害発生
        with self.inject_error_at_iteration(3):
            # When: 複数回反復が必要なコード処理
            result = await self.code_review_system.process(complex_code)
            # Then: エラー回復または適切な終了処理
```

## 🔧 デバッグ・トラブルシューティング

### エラー情報の構造化
```python
class StructuredErrorInfo:
    def __init__(self, error: Exception, context: Dict[str, Any]):
        self.error_id = str(uuid.uuid4())
        self.timestamp = datetime.utcnow().isoformat()
        self.error_type = type(error).__name__
        self.error_message = str(error)
        self.context = context
        self.stack_trace = traceback.format_exc()
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "error_id": self.error_id,
            "timestamp": self.timestamp,
            "error_type": self.error_type,
            "error_message": self.error_message,
            "context": self.context,
            "stack_trace": self.stack_trace
        }
```

---
*作成日: 2025-07-06*  
*バージョン: 1.0*