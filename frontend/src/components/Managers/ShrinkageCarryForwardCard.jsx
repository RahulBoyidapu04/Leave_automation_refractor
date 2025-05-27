import React, { useEffect, useMemo, useState } from 'react';
import axios from 'axios';
import toast from 'react-hot-toast';

const ShrinkageCarryForwardCard = ({ user, refreshKey, colorTheme = 'vibrant', theme }) => {
  const [report, setReport] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const now = useMemo(() => new Date(), []);
  const year = now.getFullYear();
  const month = now.getMonth() + 1;

  useEffect(() => {
    const fetchReport = async () => {
      setLoading(true);
      try {
        const res = await axios.get('/api/v1/leave/shrinkage/weekly-carry-forward', {
          params: { year, month },
          headers: { Authorization: `Bearer ${user?.token}` }
        });
        const data = res.data?.data || {};
        setReport(data);
        if (data.weeks?.length === 0) toast('📭 No shrinkage data for this month');
        setError(null);
      } catch (err) {
        setError(err?.response?.data?.detail || 'Failed to fetch shrinkage report');
      } finally {
        setLoading(false);
      }
    };
    if (user?.token) fetchReport();
  }, [user, year, month, refreshKey]);

  const exportToCSV = () => {
    if (!report?.weeks?.length) return;
    const rows = [
      ['Week', 'Date Range', 'Shrinkage %', 'Status'],
      ...report.weeks.map((w, i) => [`Week ${i + 1}`, w.week_range, `${w.shrinkage.toFixed(2)}%`, w.status])
    ];
    const csv = rows.map(r => r.join(',')).join('\n');
    const blob = new Blob([csv], { type: 'text/csv' });
    const link = document.createElement('a');
    link.href = URL.createObjectURL(blob);
    link.download = `Shrinkage_Report_${year}_${month}.csv`;
    link.click();
    toast.success('Exported CSV');
  };

  const statusColor = {
    Safe: 'text-green-700',
    Tight: 'text-yellow-700',
    Overbooked: 'text-red-700',
    Exceeded: 'text-red-700'
  };

  const statusIcon = {
    Safe: '✅',
    Tight: '⚠️',
    Overbooked: '❌',
    Exceeded: '❌'
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-8">
        <div className={`animate-spin rounded-full h-8 w-8 border-b-2 ${theme?.spinner || 'border-indigo-500'}`} />
        <span className={`ml-3 text-sm font-medium ${theme?.text || 'text-indigo-700'}`}>Loading shrinkage...</span>
      </div>
    );
  }

  if (error) {
    return (
      <div className="text-sm text-red-600 bg-red-50 border border-red-200 p-4 rounded-lg">
        ⚠️ {error}
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <div className={`p-2 rounded-lg bg-gradient-to-r ${theme?.cardAccent || 'from-indigo-500 to-purple-500'} shadow-sm`}>
            <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3a2 2 0 012-2h4a2 2 0 012 2v4m-6 4v10m6-10v10m6-2a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </div>
          <div>
            <h2 className={`text-xl font-bold ${theme?.text || 'text-indigo-700'} drop-shadow-sm`}>
              Shrinkage Carry Forward
            </h2>
            <p className="text-sm text-gray-500 mt-1">
              Week-wise status for {month}/{year}
            </p>
          </div>
        </div>

        {report?.status === 'Exceeded' && (
          <div className="px-3 py-1 rounded-full text-xs font-medium bg-red-100 text-red-700 shadow-sm">
            ⚠️ Exceeded Limit
          </div>
        )}
      </div>

      {/* Summary */}
      <div className="space-y-1 text-sm text-gray-700">
        <p>
          Cumulative Used: <span className="font-semibold">{report?.cumulative_used?.toFixed(2)}%</span> / 
          Target: <span className="font-semibold">{report?.monthly_target?.toFixed(2)}%</span>
        </p>
        <p className="text-blue-700">
          Carry Forward: {report?.carry_forward?.toFixed(2)}%
        </p>
        {report?.note && <p className="text-xs text-gray-500 italic">{report.note}</p>}
      </div>

      {/* Export Button */}
      <div>
        <button
          onClick={exportToCSV}
          disabled={!report?.weeks?.length}
          className={`text-sm px-4 py-2 rounded font-medium transition-all duration-200 shadow-sm ${
            report?.weeks?.length
              ? `bg-gradient-to-r ${theme?.button || 'from-indigo-500 to-purple-500'} text-white hover:scale-105`
              : 'bg-gray-300 text-gray-500 cursor-not-allowed'
          }`}
        >
          {report?.weeks?.length ? 'Export CSV' : 'Export Unavailable'}
        </button>
      </div>

      {/* Table */}
      {report?.weeks?.length > 0 ? (
        <div className={`overflow-x-auto rounded-lg border shadow-sm ${theme?.cardGradient || 'bg-gradient-to-r from-indigo-50 to-purple-50'}`}>
          <table className="min-w-full text-sm">
            <thead className="bg-white/60 text-gray-700">
              <tr>
                <th className="px-4 py-2 text-left">Week</th>
                <th className="px-4 py-2 text-left">Date Range</th>
                <th className="px-4 py-2 text-left">Shrinkage %</th>
                <th className="px-4 py-2 text-left">Status</th>
              </tr>
            </thead>
            <tbody>
              {report.weeks.map((week, idx) => (
                <tr key={idx} className={idx % 2 === 0 ? 'bg-white/40' : 'bg-white/20'}>
                  <td className="px-4 py-2">Week {idx + 1}</td>
                  <td className="px-4 py-2">{week.week_range}</td>
                  <td className="px-4 py-2">{week.shrinkage?.toFixed(2)}%</td>
                  <td className={`px-4 py-2 font-semibold ${statusColor[week.status] || ''}`}>
                    {statusIcon[week.status]} {week.status}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : (
        <div className="text-center p-4 bg-gray-50 border rounded text-sm text-gray-600">
          No weekly data available for this month.
        </div>
      )}
    </div>
  );
};

export default ShrinkageCarryForwardCard;
