"use client"

import { useState, useRef, useEffect } from 'react';
import { Send, Bot, User, AlertTriangle, FileText, Scale } from 'lucide-react';
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card } from "@/components/ui/card";
import { ScrollArea } from "@/components/ui/scroll-area";
import { GraphVisualizer } from "@/components/GraphVisualizer";
import { ReferencePanel } from "@/components/ReferencePanel";
import { ConfidenceMeter } from "@/components/ConfidenceMeter";
import { DeepDiveModal } from "@/components/DeepDiveModal";
import { cn } from '@/lib/utils';

interface Reference {
  text: string;
  metadata: {
    title: string;
    article_number: string;
    regulation: string;
    source?: string;
  };
  score?: number;
  node_id?: string;
}

interface Message {
  role: 'user' | 'assistant';
  content: string;
  // History State
  timestamp?: number;
  context?: Reference[];
  graph_data?: any;
  confidence?: number;
}

interface ApiResponse {
  answer: string;
  confidence: number;
  context: Reference[];
  graph_data: any;
}

export default function Home() {
  const [messages, setMessages] = useState<Message[]>([
    { role: 'assistant', content: 'Hello! I am your EU AI Act & GDPR Compliance Assistant. Ask me anything.' }
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [lastResponse, setLastResponse] = useState<ApiResponse | null>(null);

  // Regulation Filter State
  const [regulationFilter, setRegulationFilter] = useState<'All' | 'GDPR' | 'AI Act'>('All');

  // Modal State
  const [selectedRef, setSelectedRef] = useState<Reference | null>(null);
  const [modalOpen, setModalOpen] = useState(false);

  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth", block: "nearest" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, loading]);

  const handleSend = async () => {
    if (!input.trim()) return;

    const userMsg = input;
    setInput('');
    setMessages(prev => [...prev, { role: 'user', content: userMsg }]);
    setLoading(true);

    // Initial empty assistant message for streaming
    setMessages(prev => [...prev, { role: 'assistant', content: '' }]);

    // Temp vars to accumulate metadata during stream
    let streamContext: Reference[] = [];
    let streamGraphData: any = null;
    let streamConfidence = 0;

    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
      const res = await fetch(`${apiUrl}/api/chat/stream`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          query: userMsg,
          regulation: regulationFilter === 'All' ? null : regulationFilter
        })
      });

      if (!res.ok) throw new Error('Failed to fetch response');
      if (!res.body) throw new Error('No response body');

      const reader = res.body.getReader();
      const decoder = new TextDecoder();
      let assistantMsg = '';
      let buffer = '';

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value, { stream: true });
        buffer += chunk;

        const lines = buffer.split('\n');
        buffer = lines.pop() || '';

        for (const line of lines) {
          if (!line.trim()) continue;
          try {
            const data = JSON.parse(line);

            if (data.type === 'metadata') {
              // Update global state immediately for "live" feel
              setLastResponse({
                answer: "",
                confidence: data.confidence,
                context: data.context,
                graph_data: data.graph_data
              });

              // Store locally to attach to message later
              streamContext = data.context;
              streamGraphData = data.graph_data;
              streamConfidence = data.confidence;

            } else if (data.type === 'token') {
              assistantMsg += data.content;
              setMessages(prev => {
                const newMsgs = [...prev];
                const last = newMsgs[newMsgs.length - 1];
                if (last.role === 'assistant') {
                  last.content = assistantMsg;
                  // Attach metadata to the message so it's saved in history
                  last.context = streamContext;
                  last.graph_data = streamGraphData;
                  last.confidence = streamConfidence;
                }
                return newMsgs;
              });
            } else if (data.type === 'error') {
              assistantMsg += `\n[Error: ${data.content}]`;
            }
          } catch (e) { console.warn("Parse error", e); }
        }
      }

    } catch (error) {
      console.error(error);
      setMessages(prev => {
        const newMsgs = [...prev];
        const last = newMsgs[newMsgs.length - 1];
        if (last.role === 'assistant') {
          last.content += "\n[Connection Error]";
          return newMsgs;
        }
        return [...prev, { role: 'assistant', content: "Error connecting to server." }];
      });
    } finally {
      setLoading(false);
    }
  };

  const handleReferenceSelect = (ref: Reference) => {
    setSelectedRef(ref);
    setModalOpen(true);
  };

  const handleNodeSelect = (nodeId: string) => {
    if (!lastResponse?.context) return;

    const found = lastResponse.context.find(r => {
      if (r.node_id === nodeId) return true;
      const constructedId = `${r.metadata.regulation}_${r.metadata.article_number}`;
      return constructedId === nodeId || nodeId.includes(r.metadata.article_number);
    });

    if (found) {
      handleReferenceSelect(found);
    } else {
      console.log("Node text not in retrieved context:", nodeId);
    }
  };

  const restoreHistory = (msg: Message) => {
    if (msg.context && msg.graph_data) {
      setLastResponse({
        answer: msg.content,
        confidence: msg.confidence || 0,
        context: msg.context,
        graph_data: msg.graph_data
      });
    }
  };

  return (
    <div className="h-screen w-screen bg-background flex flex-col overflow-hidden">
      <DeepDiveModal
        reference={selectedRef}
        open={modalOpen}
        onOpenChange={setModalOpen}
      />

      {/* Header */}
      <header className="h-14 border-b px-6 flex items-center justify-between bg-card z-10 shrink-0">
        <div className="flex items-center gap-2">
          <Bot className="h-6 w-6 text-primary" />
          <h1 className="font-bold text-lg">EU AI & GDPR Compliance Advisor</h1>
        </div>

        <div className="flex items-center gap-6">
          {/* Regulation Filter */}
          <div className="flex bg-muted rounded-md p-1 h-8 items-center">
            {(['All', 'GDPR', 'AI Act'] as const).map(reg => (
              <button
                key={reg}
                onClick={() => setRegulationFilter(reg)}
                className={cn(
                  "px-3 py-1 text-xs font-medium rounded-sm transition-all",
                  regulationFilter === reg
                    ? "bg-background text-foreground shadow-sm"
                    : "text-muted-foreground hover:text-foreground"
                )}
              >
                {reg}
              </button>
            ))}
          </div>

          {lastResponse && (
            <div className="flex items-center gap-2 border-l pl-6">
              <ConfidenceMeter score={lastResponse.confidence} />
            </div>
          )}
        </div>
      </header>

      {/* Main Content Grid */}
      <div className="flex-1 grid grid-cols-12 gap-0 overflow-hidden">

        {/* LEFT: Chat Area (4 cols) */}
        <div className="col-span-4 border-r flex flex-col min-w-[350px] h-full overflow-hidden">
          <ScrollArea className="flex-1 p-4">
            <div className="space-y-4">
              {messages.map((m, i) => {
                if (m.role === 'assistant' && !m.content) return null;
                return (
                  <div key={i} className={`flex gap-3 ${m.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                    {m.role === 'assistant' && (
                      <div className="h-8 w-8 rounded-full bg-primary/10 flex items-center justify-center shrink-0">
                        <Bot className="h-5 w-5 text-primary" />
                      </div>
                    )}
                    <div className={cn(
                      "p-3 rounded-lg max-w-[85%] text-sm whitespace-pre-wrap flex flex-col gap-2 transition-all",
                      m.role === 'user' ? 'bg-primary text-primary-foreground' : 'bg-muted'
                    )}>
                      {m.content}

                      {/* History Button */}
                      {m.role === 'assistant' && m.context && (
                        <Button
                          variant="ghost"
                          size="sm"
                          className="h-6 text-[10px] self-start opacity-70 hover:opacity-100 -ml-2 text-muted-foreground hover:text-foreground hover:bg-black/5"
                          onClick={() => restoreHistory(m)}
                          title="View Sources for this answer"
                        >
                          <Scale className="h-3 w-3 mr-1" />
                          View Sources
                        </Button>
                      )}
                    </div>
                  </div>
                );
              })}
              {loading && messages[messages.length - 1].content === '' && (
                <div className="flex gap-3">
                  <div className="h-8 w-8 rounded-full bg-primary/10 flex items-center justify-center">
                    <Bot className="h-5 w-5 text-primary animate-pulse" />
                  </div>
                  <div className="p-3 rounded-lg bg-muted text-sm text-muted-foreground animate-pulse">
                    Thinking & Analyzing Graph...
                  </div>
                </div>
              )}
              {/* Invisible element to scroll to */}
              <div ref={messagesEndRef} />
            </div>
          </ScrollArea>

          {/* Input Area */}
          <div className="p-4 border-t bg-card shrink-0">
            <form
              onSubmit={(e) => { e.preventDefault(); handleSend(); }}
              className="flex gap-2"
            >
              <Input
                placeholder="Ask a legal question..."
                value={input}
                onChange={e => setInput(e.target.value)}
                disabled={loading}
              />
              <Button type="submit" disabled={loading || !input.trim()}>
                <Send className="h-4 w-4" />
              </Button>
            </form>
          </div>
        </div>

        {/* MIDDLE: Graph Viz (5 cols) */}
        <div className="col-span-5 border-r bg-gray-50/50 p-4 flex flex-col h-full overflow-hidden">
          <h2 className="text-sm font-semibold mb-2 text-muted-foreground shrink-0">Citation Graph</h2>
          <div className="flex-1 bg-white rounded-lg shadow-sm border overflow-hidden relative">
            <GraphVisualizer
              data={lastResponse?.graph_data || { nodes: [], edges: [] }}
              onNodeSelect={handleNodeSelect}
            />
          </div>
        </div>

        {/* RIGHT: Reference Panel (3 cols) */}
        <div className="col-span-3 bg-card p-4 flex flex-col min-w-[250px] h-full overflow-hidden">
          <h2 className="text-sm font-semibold mb-2 text-muted-foreground shrink-0">Retrieved Context</h2>
          <div className="flex-1 overflow-hidden min-h-0">
            <ReferencePanel
              references={lastResponse?.context || []}
              onSelectReference={handleReferenceSelect}
            />
          </div>
        </div>

      </div>
    </div>
  );
}
