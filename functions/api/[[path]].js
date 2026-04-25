export async function onRequest(context) {
  const url = new URL(context.request.url);
  
  // 直連 OCI Nginx (443 HTTPS)，繞過 Cloudflare DNS 避免無限循環
  // 使用 IP 直連 + Host header
  const backendUrl = `https://140.245.126.35${url.pathname}${url.search}`;
  
  // 準備 fetch 選項
  const fetchOptions = {
    method: context.request.method,
    redirect: 'follow',
    headers: {
      'Host': 'ewi.paul720810.dpdns.org',
      'Content-Type': context.request.headers.get('Content-Type') || 'application/json',
      'Accept': 'application/json',
    }
  };

  // 只有在非 GET/HEAD 請求時才添加 body
  if (context.request.method !== "GET" && context.request.method !== "HEAD") {
    fetchOptions.body = await context.request.arrayBuffer();
  }

  // 處理 CORS preflight
  if (context.request.method === "OPTIONS") {
    return new Response(null, {
      status: 204,
      headers: {
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
        "Access-Control-Allow-Headers": "Content-Type, Authorization",
        "Access-Control-Max-Age": "86400",
      }
    });
  }

  try {
    const response = await fetch(backendUrl, fetchOptions);

    // 複製響應並添加 CORS
    const newHeaders = new Headers(response.headers);
    newHeaders.set("Access-Control-Allow-Origin", "*");
    newHeaders.set("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS");
    newHeaders.set("Access-Control-Allow-Headers", "Content-Type");
    
    return new Response(response.body, {
      status: response.status,
      statusText: response.statusText,
      headers: newHeaders
    });
  } catch (error) {
    return new Response(JSON.stringify({ 
      error: `Backend connection failed: ${error.message}`,
      target: backendUrl 
    }), { 
      status: 502,
      headers: { "Content-Type": "application/json", "Access-Control-Allow-Origin": "*" }
    });
  }
}
