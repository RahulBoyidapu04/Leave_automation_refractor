import React, { useEffect, useState } from 'react';
import axios from 'axios';

const ShrinkageCarryForwardCard = ({ user }) => {
  const [report, setReport] = useState(null);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(true);

  const now = new Date();
  const year = now.getFullYear();
  const month = now.getMonth() + 1;

  useEffect(() => {
    const fetchReport = async () => {
      setLoading(true);
      try {
        const res = await axios.get('/manager/monthly-shrinkage', {
          params: { year, month },
          headers: { Authorization: `Bearer ${user?.token}` },
        });
        setReport(res.data);
        setError(null);
      } catch (err) {
        setError('Failed to fetch shrinkage report');
        console.error(err);
      } finally {
        setLoading(false);
      }
    };

    if (user?.token) {
      fetchReport();
    }
  }, [user, year, month]);

  const exportToCSV = (reportData) => {
    if (!reportData || !reportData.weeks) return;

    const rows = [
      ["Week", "Date Range", "Shrinkage %", "Status"],
      ...reportData.weeks.map((week, idx) => [
        `Week ${idx + 1}`,
        week.week_range,
        `${week.shrinkage}%`,
        week.status,
      ]),
    ];

    const csvContent = rows.map(e => e.join(",")).join("\n");
    const blob = new Blob([csvContent], { type: "text/csv;charset=utf-8;" });
    const link = document.createElement("a");
    link.href = URL.createObjectURL(blob);
    link.download = `Shrinkage_Report_${year}_${month}.csv`;
    link.click();
  };

  const statusColor = {
    Safe: 'text-green-600',
    Tight: 'text-amber-600',
    Overbooked: 'text-red-600',
    Exceeded: 'text-red-600'
  };

  const statusIcon = {
    Safe: '✅',
    Tight: '⚠️',
    Overbooked: '❌',
    Exceeded: '❌'
  };

  if (loading) return <div className="text-sm text-gray-500">Loading...</div>;
  if (error) return <div className="text-sm text-red-600">{error}</div>;
  if (!report) return <div className="text-sm text-gray-500">No data available.</div>;

  return (
    <div className="bg-white shadow rounded-xl p-6">
      <div className="flex justify-between items-center mb-3">
        <h2 className="text-lg font-semibold text-gray-800">Shrinkage Carry Forward</h2>
        {report.status === 'Exceeded' && (
          <span className="text-sm text-red-700 bg-red-100 px-3 py-1 rounded">
            ⚠️ Exceeds Monthly Limit
          </span>
        )}
      </div>

      <p className="text-sm text-gray-700 mb-1">
        Cumulative Used: {report.cumulative_used}% / Monthly Target: {report.monthly_target}%
      </p>
      <p className="text-sm text-blue-700 mb-4">
        Carry Forward Balance: {report.carry_forward?.toFixed(2)}%
      </p>

      <button
        onClick={() => exportToCSV(report)}
        className="text-sm bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded shadow mb-4"
      >
        Export CSV
      </button>

      <div className="overflow-x-auto">
        <table className="min-w-full bg-white border border-gray-200 text-sm rounded-md shadow-sm">
          <thead className="bg-gray-100 text-gray-700">
            <tr>
              <th className="px-4 py-2 text-left">Week</th>
              <th className="px-4 py-2 text-left">Date Range</th>
              <th className="px-4 py-2 text-left">Shrinkage %</th>
              <th className="px-4 py-2 text-left">Status</th>
            </tr>
          </thead>
          <tbody>
            {(report.weeks || []).map((week, idx) => (
              <tr key={idx} className="border-t border-gray-100">
                <td className="px-4 py-2">Week {idx + 1}</td>
                <td className="px-4 py-2">{week.week_range}</td>
                <td className="px-4 py-2">{week.shrinkage}%</td>
                <td className={`px-4 py-2 font-semibold ${statusColor[week.status]}`}>
                  {statusIcon[week.status]} {week.status}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default ShrinkageCarryForwardCard;
