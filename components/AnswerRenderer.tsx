"use client";
import React from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

export default function AnswerRenderer({ text }: { text: string }) {
    return (
        <div className="max-w-none">
            <ReactMarkdown
                remarkPlugins={[remarkGfm]}
                components={{
                    p: ({ node, ...props }) => (
                        <p className="my-2 leading-relaxed" {...props} />
                    ),
                    ul: ({ node, ...props }) => (
                        <ul className="my-2 ml-5 list-disc" {...props} />
                    ),
                    ol: ({ node, ...props }) => (
                        <ol className="my-2 ml-5 list-decimal" {...props} />
                    ),
                    li: ({ node, ...props }) => <li className="my-1" {...props} />,
                    strong: ({ node, ...props }) => (
                        <strong className="font-semibold" {...props} />
                    ),
                }}
            >
                {text}
            </ReactMarkdown>
        </div>
    );
}
