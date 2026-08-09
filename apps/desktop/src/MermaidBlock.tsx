import { useEffect, useId, useState } from "react";

const mermaidRuntime = import("mermaid").then(({ default: mermaid }) => {
  mermaid.initialize({
    startOnLoad: false,
    securityLevel: "strict",
    theme: "neutral",
    fontFamily: "Inter, 'Noto Sans SC', sans-serif",
    suppressErrorRendering: true,
  });
  return mermaid;
});

export function MermaidBlock({ chart }: { chart: string }) {
  const reactId = useId().replace(/[^a-zA-Z0-9]/g, "");
  const [svg, setSvg] = useState("");
  const [failed, setFailed] = useState(false);

  useEffect(() => {
    let active = true;
    const unsafe = /\b(click|href)\b|<\/?(?:script|iframe|object|embed)\b/i.test(chart);
    if (unsafe) {
      setFailed(true);
      return () => { active = false; };
    }
    void mermaidRuntime
      .then((mermaid) => mermaid.render(`study-chart-${reactId}`, chart))
      .then(({ svg: rendered }) => {
        if (active) {
          setSvg(rendered);
          setFailed(false);
        }
      })
      .catch(() => {
        if (active) setFailed(true);
      });
    return () => { active = false; };
  }, [chart, reactId]);

  if (failed) {
    return (
      <details className="mermaid-fallback">
        <summary>图表无法渲染，查看原始描述</summary>
        <pre><code>{chart}</code></pre>
      </details>
    );
  }
  return svg ? (
    <div className="mermaid-chart" dangerouslySetInnerHTML={{ __html: svg }} />
  ) : (
    <div className="mermaid-loading">正在绘制图表…</div>
  );
}
