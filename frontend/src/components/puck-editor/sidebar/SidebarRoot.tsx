'use client';

import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/shadcn-ui/tabs';
import { OutlineTree } from './outline/OutlineTree';
import { BlocksPanel } from './blocks/BlocksPanel';
import { FieldsPanel } from './fields/FieldsPanel';

export function SidebarRoot() {
  return (
    <div className="h-full w-[320px] border-r bg-background">
      <Tabs defaultValue="outline" className="h-full flex flex-col">
        <TabsList className="grid grid-cols-3">
          <TabsTrigger value="outline">Outline</TabsTrigger>
          <TabsTrigger value="blocks">Blocks</TabsTrigger>
          <TabsTrigger value="fields">Fields</TabsTrigger>
        </TabsList>

        <div className="flex-1 overflow-hidden">
          <TabsContent value="outline" className="h-full">
            <OutlineTree />
          </TabsContent>

          <TabsContent value="blocks" className="h-full">
            <BlocksPanel />
          </TabsContent>

          <TabsContent value="fields" className="h-full">
            <FieldsPanel />
          </TabsContent>
        </div>
      </Tabs>
    </div>
  );
}