import React from 'react';
import { Badge } from './ui/badge';

interface ScoreBadgeProps {
  score: number;
  label: string;
  icon?: React.ReactNode;
  type?: 'safety' | 'convenience' | 'distance' | 'affordability' | 'composite';
  showScore?: boolean;
}

const getScoreColor = (score: number, type: string) => {
  if (type === 'safety') {
    if (score >= 85) return 'bg-[#388E3C] text-white';
    if (score >= 70) return 'bg-[#FBC02D] text-black';
    if (score >= 50) return 'bg-[#F57C00] text-white';
    return 'bg-[#D32F2F] text-white';
  }
  
  // For other types, use generic scoring
  if (score >= 80) return 'bg-[#388E3C] text-white';
  if (score >= 60) return 'bg-[#FBC02D] text-black';
  if (score >= 40) return 'bg-[#F57C00] text-white';
  return 'bg-[#D32F2F] text-white';
};

export function ScoreBadge({ 
  score, 
  label, 
  icon, 
  type = 'composite',
  showScore = true 
}: ScoreBadgeProps) {
  const colorClass = getScoreColor(score, type);
  
  return (
    <Badge 
      className={`${colorClass} flex items-center gap-1 px-2 py-1`}
      variant="secondary"
    >
      {icon && <span className="text-sm">{icon}</span>}
      <span className="text-xs">{label}</span>
      {showScore && (
        <span className="ml-1 font-mono">{Math.round(score)}</span>
      )}
    </Badge>
  );
}
