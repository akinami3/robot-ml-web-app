import { useState, useRef, useEffect } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Card, CardHeader, CardTitle, CardContent, Button, Input } from "@/components/ui/primitives";
import { ragApi } from "@/services/api";
import { Send, Upload, FileText, Trash2, Bot, User as UserIcon, Loader2 } from "lucide-react";
import toast from "react-hot-toast";
import type { RAGDocument } from "@/types";

interface ChatMessage {
  role: "user" | "assistant";
  content: string;
}

export function RAGChatPage() {
  const queryClient = useQueryClient();
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [isStreaming, setIsStreaming] = useState(false);
  const chatEndRef = useRef<HTMLDivElement>(null);

  // Documents
  const { data: documents = [] } = useQuery<RAGDocument[]>({
    queryKey: ["rag-documents"],
    queryFn: async () => {
      const res = await ragApi.listDocuments();
      return (res.data as unknown as { items?: RAGDocument[] }).items ?? res.data;
    },
  });

  // Upload
  const uploadMut = useMutation({
    mutationFn: (file: File) => ragApi.uploadDocument(file),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["rag-documents"] });
      toast.success("Document uploaded & processed");
    },
    onError: () => toast.error("Upload failed"),
  });

  // Delete document
  const deleteMut = useMutation({
    mutationFn: (id: string) => ragApi.deleteDocument(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["rag-documents"] });
      toast.success("Document deleted");
    },
  });

  // Auto-scroll
  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  // Send query with SSE streaming
  const handleSend = async () => {
    const query = input.trim();
    if (!query || isStreaming) return;

    setInput("");
    setMessages((prev) => [...prev, { role: "user", content: query }]);
    setIsStreaming(true);

    // Add empty assistant message
    setMessages((prev) => [...prev, { role: "assistant", content: "" }]);

    try {
      const response = await fetch("/api/v1/rag/query/stream", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${localStorage.getItem("access_token") ?? ""}`,
        },
        body: JSON.stringify({ query, top_k: 5 }),
      });

      if (!response.ok) throw new Error("Query failed");

      const reader = response.body?.getReader();
      const decoder = new TextDecoder();

      if (reader) {
        let buffer = "";
        while (true) {
          const { done, value } = await reader.read();
          if (done) break;

          buffer += decoder.decode(value, { stream: true });
          const lines = buffer.split("\n");
          buffer = lines.pop() ?? "";

          for (const line of lines) {
            if (line.startsWith("data: ")) {
              const data = line.slice(6);
              if (data === "[DONE]") break;
              try {
                const parsed = JSON.parse(data);
                if (parsed.token) {
                  setMessages((prev) => {
                    const updated = [...prev];
                    const last = updated[updated.length - 1];
                    if (last.role === "assistant") {
                      last.content += parsed.token;
                    }
                    return updated;
                  });
                }
              } catch {
                // Not JSON, append as raw token
                setMessages((prev) => {
                  const updated = [...prev];
                  const last = updated[updated.length - 1];
                  if (last.role === "assistant") {
                    last.content += data;
                  }
                  return updated;
                });
              }
            }
          }
        }
      }
    } catch {
      // Fallback to non-streaming query
      try {
        const res = await ragApi.query(input || query, 5);
        setMessages((prev) => {
          const updated = [...prev];
          const last = updated[updated.length - 1];
          if (last.role === "assistant") {
            last.content = res.data.answer;
          }
          return updated;
        });
      } catch {
        setMessages((prev) => {
          const updated = [...prev];
          const last = updated[updated.length - 1];
          if (last.role === "assistant") {
            last.content = "Sorry, I couldn't process your query.";
          }
          return updated;
        });
      }
    } finally {
      setIsStreaming(false);
    }
  };

  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) uploadMut.mutate(file);
    e.target.value = "";
  };

  return (
    <div className="flex h-full gap-6">
      {/* Chat */}
      <div className="flex flex-1 flex-col">
        <h1 className="mb-4 text-2xl font-bold">RAG Chat</h1>

        <Card className="flex flex-1 flex-col overflow-hidden">
          {/* Messages */}
          <CardContent className="flex-1 space-y-4 overflow-auto p-4">
            {messages.length === 0 && (
              <div className="flex h-full items-center justify-center text-muted-foreground">
                <p>Ask questions about your uploaded documents.</p>
              </div>
            )}
            {messages.map((msg, i) => (
              <div key={i} className={`flex gap-3 ${msg.role === "user" ? "justify-end" : ""}`}>
                {msg.role === "assistant" && (
                  <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-primary/10">
                    <Bot className="h-4 w-4 text-primary" />
                  </div>
                )}
                <div
                  className={`max-w-[80%] rounded-lg px-4 py-2 text-sm ${
                    msg.role === "user"
                      ? "bg-primary text-primary-foreground"
                      : "bg-muted"
                  }`}
                >
                  <p className="whitespace-pre-wrap">{msg.content}</p>
                  {msg.role === "assistant" && msg.content === "" && isStreaming && (
                    <Loader2 className="h-4 w-4 animate-spin" />
                  )}
                </div>
                {msg.role === "user" && (
                  <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-muted">
                    <UserIcon className="h-4 w-4" />
                  </div>
                )}
              </div>
            ))}
            <div ref={chatEndRef} />
          </CardContent>

          {/* Input */}
          <div className="border-t p-4">
            <form
              onSubmit={(e) => {
                e.preventDefault();
                handleSend();
              }}
              className="flex gap-2"
            >
              <Input
                value={input}
                onChange={(e) => setInput(e.target.value)}
                placeholder="Ask about your documents..."
                disabled={isStreaming}
                className="flex-1"
              />
              <Button type="submit" disabled={isStreaming || !input.trim()} size="icon">
                <Send className="h-4 w-4" />
              </Button>
            </form>
          </div>
        </Card>
      </div>

      {/* Documents sidebar */}
      <div className="w-72 shrink-0">
        <Card className="h-full">
          <CardHeader className="pb-3">
            <CardTitle className="flex items-center justify-between text-base">
              <span>Documents</span>
              <label className="cursor-pointer">
                <input type="file" className="hidden" accept=".pdf,.txt,.md" onChange={handleFileUpload} />
                <div className="flex h-8 w-8 items-center justify-center rounded-md hover:bg-accent">
                  <Upload className="h-4 w-4" />
                </div>
              </label>
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-2">
            {uploadMut.isPending && (
              <div className="flex items-center gap-2 text-sm text-muted-foreground">
                <Loader2 className="h-3 w-3 animate-spin" />
                Processing...
              </div>
            )}
            {documents.length === 0 ? (
              <p className="text-xs text-muted-foreground">Upload PDF, TXT, or MD files.</p>
            ) : (
              documents.map((doc) => (
                <div key={doc.id} className="flex items-center justify-between rounded-md border p-2">
                  <div className="flex items-center gap-2 min-w-0">
                    <FileText className="h-4 w-4 shrink-0 text-muted-foreground" />
                    <div className="min-w-0">
                      <p className="truncate text-xs font-medium">{doc.title}</p>
                      <p className="text-[10px] text-muted-foreground">{doc.chunk_count ?? 0} chunks</p>
                    </div>
                  </div>
                  <Button size="icon" variant="ghost" className="h-6 w-6" onClick={() => deleteMut.mutate(doc.id)}>
                    <Trash2 className="h-3 w-3 text-destructive" />
                  </Button>
                </div>
              ))
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
