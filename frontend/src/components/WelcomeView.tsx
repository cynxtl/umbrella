import React from 'react';
import { Calendar, CloudRain, Clock, GraduationCap, Footprints, Trees } from 'lucide-react';

interface WelcomeViewProps {
  onSelectPrompt: (prompt: string) => void;
}

export const WelcomeView: React.FC<WelcomeViewProps> = ({ onSelectPrompt }) => {
  const suggestions = [
    {
      title: 'Plan my day',
      desc: 'Check general outlook for tomorrow',
      icon: Calendar,
      prompt: 'Plan my day tomorrow in Pune',
    },
    {
      title: 'Check rain risk',
      desc: 'Evaluate umbrella requirements',
      icon: CloudRain,
      prompt: 'Will it rain tomorrow in Pune? Should I carry an umbrella?',
    },
    {
      title: 'Find a better time',
      desc: 'Compare alternative windows',
      icon: Clock,
      prompt: 'I want to go for an outdoor walk tomorrow around 3 PM, find me a better time.',
    },
    {
      title: 'College schedule',
      desc: 'Commute hours 9 to 4',
      icon: GraduationCap,
      prompt: 'I have college tomorrow from 9 to 4. Will I need an umbrella?',
    },
    {
      title: 'Evening walk',
      desc: 'Activity around 5 PM',
      icon: Footprints,
      prompt: 'Going for an evening walk around 5 PM. Will it rain?',
    },
    {
      title: 'Outdoor event',
      desc: 'Afternoon exposure',
      icon: Trees,
      prompt: 'Planning an outdoor event tomorrow from 2 PM to 6 PM in Pune.',
    },
  ];

  return (
    <div className="flex flex-col items-center justify-center px-4 pt-12 pb-24 text-center">
      <div className="max-w-xl">
        <h1 className="text-3xl sm:text-4xl font-bold tracking-tight text-white mb-2.5">
          What are you planning?
        </h1>
        <p className="text-base text-text-secondary font-normal">
          A little foresight for whatever&apos;s ahead.
        </p>
      </div>

      <div className="mt-10 grid w-full max-w-2xl grid-cols-1 sm:grid-cols-2 gap-3 text-left">
        {suggestions.map((item, idx) => {
          const Icon = item.icon;
          return (
            <button
              key={idx}
              onClick={() => onSelectPrompt(item.prompt)}
              className="group flex items-start gap-3 rounded-xl border border-white/[0.08] bg-white/[0.025] p-3.5 hover:border-white/[0.22] hover:bg-white/[0.05] transition-all text-left"
            >
              <div className="mt-0.5 flex h-7 w-7 items-center justify-center rounded-lg border border-white/[0.08] bg-white/[0.03] text-text-secondary group-hover:text-white transition-colors">
                <Icon className="h-4 w-4" />
              </div>
              <div className="flex-1 min-w-0">
                <div className="text-sm font-medium text-white group-hover:text-white">
                  {item.title}
                </div>
                <div className="text-xs text-text-muted truncate mt-0.5">
                  {item.desc}
                </div>
              </div>
            </button>
          );
        })}
      </div>
    </div>
  );
};
