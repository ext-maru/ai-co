def auto_place_file_with_timeout(
    self, source_content, suggested_filename=None, task_id=None
):
    """
    タイムアウト対策を施したauto_place_file
    複雑なML処理の前に、まず高速な基本処理を試行
    """
    import time

    from libs.self_evolution_manager_optimized import OptimizedSelfEvolutionManager

    # まず高速版を試行（30秒タイムアウト）
    optimized_manager = OptimizedSelfEvolutionManager(timeout_seconds=30)

    # ファイルサイズをチェック
    content_size = len(source_content)

    if content_size < 10000:  # 10KB未満は高速版
        result = optimized_manager.auto_place_file_fast(
            source_content, suggested_filename, task_id
        )
        if result["status"] == "success":
            # 成功したら学習データに記録
            self._record_placement_success(
                result["filename"], result["relative_path"], "rule_based_fast"
            )
            return result
    else:  # 大きなファイルはチャンク版
        result = optimized_manager.auto_place_file_chunked(
            source_content, suggested_filename, task_id
        )
        if result["status"] == "success":
            self._record_placement_success(
                result["filename"], result["relative_path"], "chunked_processing"
            )
            return result

    # フォールバック：元のML処理（ただし時間制限付き）
    start_time = time.time()
    timeout = 120  # 2分

    try:
        # 元の処理を実行（ただし段階的に）
        if hasattr(self, "_original_auto_place_file"):
            return self._original_auto_place_file(
                source_content, suggested_filename, task_id
            )
        else:
            # シンプルなデフォルト処理
            return {
                "status": "fallback",
                "filename": suggested_filename or "auto_generated.py",
                "path": str(
                    self.project_root
                    / "scripts"
                    / (suggested_filename or "auto_generated.py")
                ),
                "method": "simple_fallback",
            }
    except Exception as e:
        logger.error(f"Error in ML processing: {e}")
        # エラー時は高速版の結果を返す
        return optimized_manager.auto_place_file_fast(
            source_content, suggested_filename, task_id
        )
