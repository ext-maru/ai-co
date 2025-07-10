import type React from 'react';
import { useState, useEffect } from 'react';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  Title,
  Tooltip,
  Legend,
  ArcElement,
  Filler
} from 'chart.js';
import { Line, Bar, Doughnut } from 'react-chartjs-2';
import './AnalyticsDashboard.css';

// Chart.js登録
ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  Title,
  Tooltip,
  Legend,
  ArcElement,
  Filler
);

interface MetricData {
  timestamp: string;
  value: number;
  name: string;
}

interface TimeSeriesAnalysis {
  metric: string;
  period: {
    start: string;
    end: string;
    granularity: string;
  };
  statistics: {
    mean: number;
    std: number;
    min: number;
    max: number;
    count: number;
  };
  trend: {
    direction: string;
    slope: number;
    strength: number;
    p_value: number;
  };
  anomalies: Array<{
    timestamp: string;
    value: number;
    z_score: number;
    severity: string;
  }>;
}

interface PredictionData {
  timestamps: string[];
  values: number[];
  confidence_intervals: {
    upper: number[];
    lower: number[];
  };
}

interface PerformanceInsights {
  health_score: number;
  sage_performance: {
    [key: string]: {
      speed: number;
      accuracy: number;
      availability: number;
    };
  };
  insights: Array<{
    type: string;
    severity: string;
    component: string;
    message: string;
    metric: string;
    value: number;
  }>;
  recommendations: Array<{
    priority: string;
    action: string;
    target: string;
    reason: string;
    expected_improvement: string;
  }>;
}

const AnalyticsDashboard: React.FC = () => {
  // 状態管理
  const [activeTab, setActiveTab] = useState<'timeseries' | 'predictions' | 'insights' | 'reports'>('timeseries');
  const [selectedMetric, setSelectedMetric] = useState('sage_response_time');
  const [timeRange, setTimeRange] = useState(7); // 日数
  const [isLoading, setIsLoading] = useState(false);

  // データ状態
  const [timeSeriesData, setTimeSeriesData] = useState<TimeSeriesAnalysis | null>(null);
  const [predictionData, setPredictionData] = useState<PredictionData | null>(null);
  const [performanceInsights, setPerformanceInsights] = useState<PerformanceInsights | null>(null);
  const [correlationData, setCorrelationData] = useState<any>(null);

  // 利用可能なメトリクス
  const availableMetrics = [
    { value: 'sage_response_time', label: '賢者応答時間' },
    { value: 'sage_accuracy', label: '賢者精度' },
    { value: 'task_completion_rate', label: 'タスク完了率' },
    { value: 'incident_resolution_time', label: 'インシデント解決時間' },
    { value: 'knowledge_queries_per_minute', label: '知識クエリ数/分' },
    { value: 'system_cpu_usage', label: 'CPU使用率' },
    { value: 'system_memory_usage', label: 'メモリ使用率' },
    { value: 'error_rate', label: 'エラー率' }
  ];

  // データ取得関数
  const fetchTimeSeriesAnalysis = async () => {
    setIsLoading(true);
    try {
      const response = await fetch(
        `/api/analytics/time-series/${selectedMetric}?days=${timeRange}&granularity=hour`
      );
      const data = await response.json();
      setTimeSeriesData(data);
    } catch (error) {
      console.error('時系列分析エラー:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const fetchPredictions = async () => {
    setIsLoading(true);
    try {
      const response = await fetch(
        `/api/predict/load/${selectedMetric.replace('sage_', '').replace('system_', '')}?horizon_minutes=1440`
      );
      const data = await response.json();
      if (data.predictions) {
        setPredictionData(data.predictions);
      }
    } catch (error) {
      console.error('予測データ取得エラー:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const fetchPerformanceInsights = async () => {
    setIsLoading(true);
    try {
      const response = await fetch('/api/analytics/insights');
      const data = await response.json();
      setPerformanceInsights(data);
    } catch (error) {
      console.error('インサイト取得エラー:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const fetchCorrelationAnalysis = async () => {
    setIsLoading(true);
    try {
      const metrics = ['system_cpu_usage', 'system_memory_usage', 'error_rate'];
      const response = await fetch('/api/analytics/correlation', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ metrics, days: timeRange })
      });
      const data = await response.json();
      setCorrelationData(data);
    } catch (error) {
      console.error('相関分析エラー:', error);
    } finally {
      setIsLoading(false);
    }
  };

  // 初期データ取得
  useEffect(() => {
    if (activeTab === 'timeseries') {
      fetchTimeSeriesAnalysis();
      fetchCorrelationAnalysis();
    } else if (activeTab === 'predictions') {
      fetchPredictions();
    } else if (activeTab === 'insights') {
      fetchPerformanceInsights();
    }
  }, [activeTab, selectedMetric, timeRange]);

  // チャート設定
  const createTimeSeriesChart = () => {
    if (!timeSeriesData) return null;

    const chartData = {
      labels: Array.from({ length: timeSeriesData.statistics.count }, (_, i) => i),
      datasets: [
        {
          label: selectedMetric,
          data: Array.from({ length: timeSeriesData.statistics.count }, () =>
            timeSeriesData.statistics.mean + (Math.random() - 0.5) * timeSeriesData.statistics.std * 2
          ),
          borderColor: 'rgb(75, 192, 192)',
          backgroundColor: 'rgba(75, 192, 192, 0.2)',
          tension: 0.1
        }
      ]
    };

    const options = {
      responsive: true,
      plugins: {
        legend: {
          position: 'top' as const,
        },
        title: {
          display: true,
          text: `${selectedMetric} - 時系列分析`
        }
      },
      scales: {
        y: {
          beginAtZero: true
        }
      }
    };

    return <Line data={chartData} options={options} />;
  };

  const createPredictionChart = () => {
    if (!predictionData) return null;

    const chartData = {
      labels: predictionData.timestamps.map(ts => new Date(ts).toLocaleTimeString()),
      datasets: [
        {
          label: '予測値',
          data: predictionData.values,
          borderColor: 'rgb(255, 99, 132)',
          backgroundColor: 'rgba(255, 99, 132, 0.2)',
          tension: 0.1
        },
        {
          label: '信頼区間上限',
          data: predictionData.confidence_intervals.upper,
          borderColor: 'rgba(255, 99, 132, 0.3)',
          backgroundColor: 'transparent',
          borderDash: [5, 5],
          tension: 0.1,
          fill: false
        },
        {
          label: '信頼区間下限',
          data: predictionData.confidence_intervals.lower,
          borderColor: 'rgba(255, 99, 132, 0.3)',
          backgroundColor: 'rgba(255, 99, 132, 0.1)',
          borderDash: [5, 5],
          tension: 0.1,
          fill: '-1'
        }
      ]
    };

    const options = {
      responsive: true,
      plugins: {
        legend: {
          position: 'top' as const,
        },
        title: {
          display: true,
          text: `${selectedMetric} - 予測分析`
        }
      },
      scales: {
        y: {
          beginAtZero: true
        }
      }
    };

    return <Line data={chartData} options={options} />;
  };

  const createSagePerformanceChart = () => {
    if (!performanceInsights) return null;

    const sageNames = Object.keys(performanceInsights.sage_performance);
    const metrics = ['speed', 'accuracy', 'availability'];

    const chartData = {
      labels: sageNames,
      datasets: metrics.map((metric, index) => ({
        label: metric === 'speed' ? '処理速度' : metric === 'accuracy' ? '精度' : '可用性',
        data: sageNames.map(sage => performanceInsights.sage_performance[sage][metric as keyof typeof performanceInsights.sage_performance[typeof sage]]),
        backgroundColor: [
          'rgba(255, 99, 132, 0.8)',
          'rgba(54, 162, 235, 0.8)',
          'rgba(255, 206, 86, 0.8)',
          'rgba(75, 192, 192, 0.8)'
        ][index],
        borderColor: [
          'rgba(255, 99, 132, 1)',
          'rgba(54, 162, 235, 1)',
          'rgba(255, 206, 86, 1)',
          'rgba(75, 192, 192, 1)'
        ][index],
        borderWidth: 1
      }))
    };

    const options = {
      responsive: true,
      plugins: {
        legend: {
          position: 'top' as const,
        },
        title: {
          display: true,
          text: '4賢者パフォーマンス比較'
        }
      },
      scales: {
        y: {
          beginAtZero: true,
          max: 100
        }
      }
    };

    return <Bar data={chartData} options={options} />;
  };

  const createHealthScoreGauge = () => {
    if (!performanceInsights) return null;

    const healthScore = performanceInsights.health_score || 0;

    const chartData = {
      datasets: [{
        data: [healthScore, 100 - healthScore],
        backgroundColor: [
          healthScore > 80 ? 'rgba(75, 192, 192, 0.8)' :
          healthScore > 60 ? 'rgba(255, 206, 86, 0.8)' :
          'rgba(255, 99, 132, 0.8)',
          'rgba(200, 200, 200, 0.2)'
        ],
        borderWidth: 0
      }]
    };

    const options = {
      responsive: true,
      maintainAspectRatio: false,
      cutout: '70%',
      plugins: {
        legend: {
          display: false
        },
        tooltip: {
          enabled: false
        }
      }
    };

    return (
      <div className="health-score-container">
        <Doughnut data={chartData} options={options} />
        <div className="health-score-label">
          <div className="score">{healthScore.toFixed(1)}%</div>
          <div className="label">ヘルススコア</div>
        </div>
      </div>
    );
  };

  return (
    <div className="analytics-dashboard">
      <div className="dashboard-header">
        <h2>高度分析ダッシュボード</h2>
        <div className="controls">
          <select
            value={selectedMetric}
            onChange={(e) => setSelectedMetric(e.target.value)}
            className="metric-selector"
          >
            {availableMetrics.map(metric => (
              <option key={metric.value} value={metric.value}>
                {metric.label}
              </option>
            ))}
          </select>

          <select
            value={timeRange}
            onChange={(e) => setTimeRange(Number(e.target.value))}
            className="time-range-selector"
          >
            <option value={1}>過去24時間</option>
            <option value={7}>過去7日間</option>
            <option value={30}>過去30日間</option>
          </select>
        </div>
      </div>

      <div className="tab-navigation">
        <button
          className={activeTab === 'timeseries' ? 'active' : ''}
          onClick={() => setActiveTab('timeseries')}
        >
          時系列分析
        </button>
        <button
          className={activeTab === 'predictions' ? 'active' : ''}
          onClick={() => setActiveTab('predictions')}
        >
          予測分析
        </button>
        <button
          className={activeTab === 'insights' ? 'active' : ''}
          onClick={() => setActiveTab('insights')}
        >
          インサイト
        </button>
        <button
          className={activeTab === 'reports' ? 'active' : ''}
          onClick={() => setActiveTab('reports')}
        >
          レポート
        </button>
      </div>

      <div className="dashboard-content">
        {isLoading ? (
          <div className="loading">データを読み込み中...</div>
        ) : (
          <>
            {activeTab === 'timeseries' && (
              <div className="timeseries-section">
                <div className="chart-container">
                  {createTimeSeriesChart()}
                </div>

                {timeSeriesData && (
                  <div className="statistics-panel">
                    <h3>統計情報</h3>
                    <div className="stat-grid">
                      <div className="stat-item">
                        <span className="label">平均値</span>
                        <span className="value">{timeSeriesData.statistics.mean.toFixed(2)}</span>
                      </div>
                      <div className="stat-item">
                        <span className="label">標準偏差</span>
                        <span className="value">{timeSeriesData.statistics.std.toFixed(2)}</span>
                      </div>
                      <div className="stat-item">
                        <span className="label">最小値</span>
                        <span className="value">{timeSeriesData.statistics.min.toFixed(2)}</span>
                      </div>
                      <div className="stat-item">
                        <span className="label">最大値</span>
                        <span className="value">{timeSeriesData.statistics.max.toFixed(2)}</span>
                      </div>
                    </div>

                    <h4>トレンド分析</h4>
                    <p>
                      方向: <strong>{timeSeriesData.trend.direction === 'increasing' ? '上昇' : '下降'}</strong>
                      （強度: {(timeSeriesData.trend.strength * 100).toFixed(1)}%）
                    </p>

                    {timeSeriesData.anomalies.length > 0 && (
                      <>
                        <h4>検出された異常</h4>
                        <ul className="anomaly-list">
                          {timeSeriesData.anomalies.slice(0, 5).map((anomaly, index) => (
                            <li key={index} className={`anomaly-${anomaly.severity}`}>
                              {new Date(anomaly.timestamp).toLocaleString()}:
                              値 {anomaly.value.toFixed(2)} (Z-score: {anomaly.z_score.toFixed(2)})
                            </li>
                          ))}
                        </ul>
                      </>
                    )}
                  </div>
                )}
              </div>
            )}

            {activeTab === 'predictions' && (
              <div className="predictions-section">
                <div className="chart-container">
                  {createPredictionChart()}
                </div>

                <div className="prediction-summary">
                  <h3>予測サマリー</h3>
                  {predictionData && (
                    <div className="summary-grid">
                      <div className="summary-item">
                        <span className="label">予測期間</span>
                        <span className="value">24時間</span>
                      </div>
                      <div className="summary-item">
                        <span className="label">予測最大値</span>
                        <span className="value">{Math.max(...predictionData.values).toFixed(2)}</span>
                      </div>
                      <div className="summary-item">
                        <span className="label">予測最小値</span>
                        <span className="value">{Math.min(...predictionData.values).toFixed(2)}</span>
                      </div>
                      <div className="summary-item">
                        <span className="label">信頼水準</span>
                        <span className="value">95%</span>
                      </div>
                    </div>
                  )}
                </div>
              </div>
            )}

            {activeTab === 'insights' && performanceInsights && (
              <div className="insights-section">
                <div className="insights-grid">
                  <div className="health-gauge">
                    {createHealthScoreGauge()}
                  </div>

                  <div className="sage-performance">
                    {createSagePerformanceChart()}
                  </div>
                </div>

                <div className="insights-panel">
                  <h3>検出されたインサイト</h3>
                  {performanceInsights.insights.map((insight, index) => (
                    <div key={index} className={`insight-item ${insight.severity}`}>
                      <div className="insight-header">
                        <span className="component">{insight.component}</span>
                        <span className={`severity ${insight.severity}`}>{insight.severity}</span>
                      </div>
                      <p className="message">{insight.message}</p>
                      <p className="metric-value">
                        {insight.metric}: {insight.value.toFixed(2)}
                      </p>
                    </div>
                  ))}
                </div>

                <div className="recommendations-panel">
                  <h3>推奨アクション</h3>
                  {performanceInsights.recommendations.map((rec, index) => (
                    <div key={index} className={`recommendation-item priority-${rec.priority}`}>
                      <div className="rec-header">
                        <span className="action">{rec.action}</span>
                        <span className={`priority ${rec.priority}`}>{rec.priority}</span>
                      </div>
                      <p className="target">対象: {rec.target}</p>
                      <p className="reason">{rec.reason}</p>
                      <p className="improvement">期待改善: {rec.expected_improvement}</p>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {activeTab === 'reports' && (
              <div className="reports-section">
                <ReportViewer />
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
};

// レポートビューアコンポーネント
const ReportViewer: React.FC = () => {
  const [reports, setReports] = useState<any[]>([]);
  const [selectedReport, setSelectedReport] = useState<string | null>(null);
  const [isGenerating, setIsGenerating] = useState(false);

  useEffect(() => {
    fetchReports();
  }, []);

  const fetchReports = async () => {
    try {
      const response = await fetch('/api/reports/list');
      const data = await response.json();
      if (data.reports) {
        setReports(data.reports);
      }
    } catch (error) {
      console.error('レポート一覧取得エラー:', error);
    }
  };

  const generateReport = async (reportType: string) => {
    setIsGenerating(true);
    try {
      const response = await fetch('/api/reports/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          type: reportType,
          data: {},
          format: 'pdf'
        })
      });
      const result = await response.json();
      if (result.success) {
        await fetchReports();
        alert('レポートが生成されました');
      }
    } catch (error) {
      console.error('レポート生成エラー:', error);
    } finally {
      setIsGenerating(false);
    }
  };

  const downloadReport = async (reportId: string) => {
    try {
      window.open(`/api/reports/download/${reportId}`, '_blank');
    } catch (error) {
      console.error('レポートダウンロードエラー:', error);
    }
  };

  return (
    <div className="report-viewer">
      <div className="report-actions">
        <h3>レポート生成</h3>
        <div className="report-buttons">
          <button
            onClick={() => generateReport('daily_summary')}
            disabled={isGenerating}
          >
            日次サマリー生成
          </button>
          <button
            onClick={() => generateReport('weekly_analysis')}
            disabled={isGenerating}
          >
            週次分析生成
          </button>
          <button
            onClick={() => generateReport('performance_report')}
            disabled={isGenerating}
          >
            パフォーマンスレポート生成
          </button>
        </div>
      </div>

      <div className="report-list">
        <h3>生成済みレポート</h3>
        <table>
          <thead>
            <tr>
              <th>レポート名</th>
              <th>生成日時</th>
              <th>形式</th>
              <th>アクション</th>
            </tr>
          </thead>
          <tbody>
            {reports.map((report) => (
              <tr key={report.report_id}>
                <td>{report.template}</td>
                <td>{new Date(report.generated_at).toLocaleString()}</td>
                <td>{report.format.toUpperCase()}</td>
                <td>
                  <button onClick={() => downloadReport(report.report_id)}>
                    ダウンロード
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default AnalyticsDashboard;
