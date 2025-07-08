#!/bin/bash
#!/bin/bash
echo "📌 処理後のシステム状態:"
echo ""
echo "ResultWorkerプロセス:"
ps aux | grep result_worker | grep -v grep
echo ""
echo "キュー状態:"
sudo rabbitmqctl list_queues name messages consumers | grep -E 'ai_results|result_queue'
echo ""
echo "最新ログ（最後20行）:"
tail -n 20 /home/aicompany/ai_co/logs/result_worker.log
