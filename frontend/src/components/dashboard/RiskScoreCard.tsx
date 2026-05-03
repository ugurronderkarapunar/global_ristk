// frontend/src/components/dashboard/RiskScoreCard.tsx
'use client';

import React, { useMemo } from 'react';
import { motion } from 'framer-motion';
import { TrendingUp, TrendingDown, Minus, AlertTriangle, Shield, Globe } from 'lucide-react';
import { cn } from '@/lib/utils';
import { useTranslations } from 'next-intl';

// RTL desteği için
interface RiskScoreCardProps {
  countryCode: string;
  countryName: string;
  flagEmoji: string;
  overallScore: number;
  politicalScore: number;
  economicScore: number;
  securityScore: number;
  tradeScore: number;
  trend: 'UP' | 'DOWN' | 'STABLE';
  aiSummary?: string;
  onClick?: () => void;
  className?: string;
  isRTL?: boolean;
}

const getRiskColor = (score: number): string => {
  if (score >= 70) return 'var(--risk-high, #ff4444)';
  if (score >= 40) return 'var(--risk-medium, #ffaa00)';
  return 'var(--risk-low, #00cc66)';
};

const getRiskLevel = (score: number): { label: string; color: string; icon: React.ReactNode } => {
  if (score >= 70) return { label: 'HIGH', color: '#ff4444', icon: <AlertTriangle size={16} /> };
  if (score >= 40) return { label: 'MEDIUM', color: '#ffaa00', icon: <Shield size={16} /> };
  return { label: 'LOW', color: '#00cc66', icon: <Globe size={16} /> };
};

const TrendIndicator: React.FC<{ trend: 'UP' | 'DOWN' | 'STABLE' }> = ({ trend }) => {
  switch (trend) {
    case 'UP':
      return <TrendingUp size={16} color="#ff4444" />;
    case 'DOWN':
      return <TrendingDown size={16} color="#00cc66" />;
    default:
      return <Minus size={16} color="#8899aa" />;
  }
};

export const RiskScoreCard: React.FC<RiskScoreCardProps> = ({
  countryCode,
  countryName,
  flagEmoji,
  overallScore,
  politicalScore,
  economicScore,
  securityScore,
  tradeScore,
  trend,
  aiSummary,
  onClick,
  className,
  isRTL = false,
}) => {
  const riskInfo = useMemo(() => getRiskLevel(overallScore), [overallScore]);
  const riskColor = useMemo(() => getRiskColor(overallScore), [overallScore]);
  const t = useTranslations('dashboard');

  // Skor bar'ları için renk hesaplama
  const subScores = [
    { label: t('political'), value: politicalScore, color: getRiskColor(politicalScore) },
    { label: t('economic'), value: economicScore, color: getRiskColor(economicScore) },
    { label: t('security'), value: securityScore, color: getRiskColor(securityScore) },
    { label: t('trade'), value: tradeScore, color: getRiskColor(tradeScore) },
  ];

  return (
    <motion.div
      whileHover={{ scale: 1.02, y: -4 }}
      whileTap={{ scale: 0.98 }}
      onClick={onClick}
      className={cn(
        'relative overflow-hidden rounded-2xl cursor-pointer',
        'bg-gradient-to-br from-[#1a1f2e] via-[#151a26] to-[#111620]',
        'border border-[#2a3040] hover:border-[#3a8bff]',
        'shadow-lg shadow-black/20 hover:shadow-xl hover:shadow-[#3a8bff]/10',
        'transition-all duration-300 ease-out',
        'p-6 w-full max-w-[380px]',
        isRTL ? 'text-right' : 'text-left',
        className
      )}
      style={{ direction: isRTL ? 'rtl' : 'ltr' }}
    >
      {/* Arka plan glow efekti */}
      <div
        className="absolute -top-10 -right-10 w-40 h-40 rounded-full blur-3xl opacity-20"
        style={{ backgroundColor: riskColor }}
      />

      {/* Başlık */}
      <div className="flex items-center justify-between mb-4 relative z-10">
        <div className="flex items-center gap-2">
          <span className="text-2xl">{flagEmoji}</span>
          <div>
            <h3 className="text-white font-semibold text-lg leading-tight">{countryName}</h3>
            <span className="text-[#6b7280] text-xs uppercase tracking-wider">{countryCode}</span>
          </div>
        </div>
        <TrendIndicator trend={trend} />
      </div>

      {/* Ana Risk Puanı */}
      <div className="text-center mb-6 relative z-10">
        <div
          className="text-7xl font-bold tracking-tighter"
          style={{ color: riskColor }}
        >
          {overallScore}
          <span className="text-2xl text-[#6b7280]">/100</span>
        </div>
        <div
          className="inline-flex items-center gap-1 mt-1 px-3 py-1 rounded-full text-xs font-semibold uppercase tracking-wider"
          style={{
            backgroundColor: `${riskColor}20`,
            color: riskColor,
            border: `1px solid ${riskColor}40`,
          }}
        >
          {riskInfo.icon}
          {riskInfo.label}
        </div>
      </div>

      {/* Alt Skorlar */}
      <div className="space-y-2.5 mb-4 relative z-10">
        {subScores.map((sub) => (
          <div key={sub.label} className="flex items-center gap-2">
            <span className="text-[#8899aa] text-xs w-20 truncate">
              {sub.label}
            </span>
            <div className="flex-1 h-2 bg-[#1e2433] rounded-full overflow-hidden">
              <motion.div
                initial={{ width: 0 }}
                animate={{ width: `${sub.value}%` }}
                transition={{ duration: 0.8, ease: 'easeOut' }}
                className="h-full rounded-full"
                style={{ backgroundColor: sub.color }}
              />
            </div>
            <span className="text-white text-xs font-mono w-8 text-right">
              {sub.value}
            </span>
          </div>
        ))}
      </div>

      {/* AI Özeti */}
      {aiSummary && (
        <div className="mt-4 pt-4 border-t border-[#2a3040] relative z-10">
          <p className="text-[#6b7280] text-xs leading-relaxed line-clamp-2">
            🤖 {aiSummary}
          </p>
        </div>
      )}
    </motion.div>
  );
};

export default RiskScoreCard;
