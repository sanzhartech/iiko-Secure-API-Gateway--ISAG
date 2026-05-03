import React from 'react';
import { RadialBarChart, RadialBar, ResponsiveContainer, PolarAngleAxis } from 'recharts';

interface SecurityScoreProps {
  score: number; // 0 to 100
}

export const SecurityScore: React.FC<SecurityScoreProps> = ({ score }) => {
  const data = [
    {
      name: 'Score',
      value: score,
      fill: 'url(#scoreGradient)',
    }
  ];

  return (
    <div className="glass-card" style={{ height: '350px', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', position: 'relative' }}>
      <h3 style={{ position: 'absolute', top: '24px', left: '24px', color: 'var(--text-secondary)', fontSize: '0.9rem', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
        Security Score
      </h3>
      <div style={{ width: '100%', height: '220px', marginTop: '20px' }}>
        <ResponsiveContainer width="100%" height="100%">
          <RadialBarChart 
            cx="50%" 
            cy="50%" 
            innerRadius="70%" 
            outerRadius="100%" 
            barSize={16} 
            data={data}
            startAngle={180}
            endAngle={0}
          >
            <defs>
              <linearGradient id="scoreGradient" x1="0" y1="0" x2="1" y2="0">
                <stop offset="0%" stopColor="var(--accent-cyan)" />
                <stop offset="100%" stopColor="#a855f7" /> {/* Purple blend */}
              </linearGradient>
            </defs>
            <PolarAngleAxis 
              type="number" 
              domain={[0, 100]} 
              angleAxisId={0} 
              tick={false} 
            />
            <RadialBar
              background={{ fill: 'rgba(255, 255, 255, 0.05)' }}
              dataKey="value"
              cornerRadius={10}
              isAnimationActive={true}
              animationDuration={1500}
              animationEasing="ease-out"
            />
          </RadialBarChart>
        </ResponsiveContainer>
      </div>
      <div style={{ position: 'absolute', bottom: '60px', textAlign: 'center' }}>
        <div style={{ fontSize: '3rem', fontWeight: 700, color: 'var(--text-primary)', lineHeight: 1 }}>
          {score}%
        </div>
        <div style={{ color: 'var(--accent-cyan)', fontSize: '0.85rem', fontWeight: 600, marginTop: '4px', textTransform: 'uppercase', letterSpacing: '0.1em' }}>
          Optimal
        </div>
      </div>
    </div>
  );
};

export default SecurityScore;
