"use client"

import React from 'react';
import { IconBuildingStore, IconPencil, IconSettings, IconBriefcase } from '@tabler/icons-react';
import { Card, CardContent } from '@/components/shadcn-ui/card';
import { Badge } from '@/components/shadcn-ui/badge';

import type { WorkspaceType } from '@/types/workspace/core';

export interface WorkspaceTypeCardProps {
  type: WorkspaceType;
  title: string;
  description: string;
  features: string[];
  isSelected: boolean;
  onSelect: (type: WorkspaceType) => void;
  disabled?: boolean;
}

const typeIcons = {
  store: IconBuildingStore,
  blog: IconPencil,
  services: IconSettings,
  portfolio: IconBriefcase,
};

const typeColors = {
  store: 'bg-blue-50 border-blue-200 text-blue-700',
  blog: 'bg-green-50 border-green-200 text-green-700',
  services: 'bg-purple-50 border-purple-200 text-purple-700',
  portfolio: 'bg-orange-50 border-orange-200 text-orange-700',
};

export function WorkspaceTypeCard({
  type,
  title,
  description,
  features,
  isSelected,
  onSelect,
  disabled = false,
}: WorkspaceTypeCardProps) {
  const Icon = typeIcons[type];
  const colorClass = typeColors[type];

  return (
    <Card
      className={`
        cursor-pointer transition-all duration-200 border-2
        ${isSelected
          ? 'border-primary ring-2 ring-primary/20 bg-primary/5'
          : 'border-border hover:border-primary/50 hover:bg-muted/50'
        }
        ${disabled ? 'opacity-50 cursor-not-allowed' : ''}
      `}
      onClick={() => !disabled && onSelect(type)}
    >
      <CardContent className="p-6">
        <div className="flex items-start gap-4">
          <div className={`p-3 rounded-lg ${colorClass}`}>
            <Icon className="h-6 w-6" />
          </div>

          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 mb-2">
              <h3 className="font-semibold text-lg">{title}</h3>
              {disabled && (
                <Badge variant="secondary" className="text-xs">
                  Upgrade Required
                </Badge>
              )}
            </div>

            <p className="text-muted-foreground text-sm mb-4">
              {description}
            </p>

            <div className="space-y-1">
              {features.map((feature, index) => (
                <div key={index} className="flex items-center gap-2 text-sm">
                  <div className="w-1.5 h-1.5 bg-primary rounded-full"></div>
                  <span className="text-muted-foreground">{feature}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}