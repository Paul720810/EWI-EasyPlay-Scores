export async function onRequest(context) {
  const url = new URL(context.request.url);
  
  // 將所有 /api/* 的請求轉發到 OCI 後端
  const backendUrl = `http://140.245.126.35:8001${url.pathname}${url.search}`;
  
  // 複製原始請求的 header
  const headers = new Headers(context.request.headers);
  headers.delete("Host");

  // 準備 fetch 選項
  const fetchOptions = {
    method: context.request.method,
    headers: headers,
    redirect: 'follow'
  };

  // 只有在非 GET/HEAD 請求時才添加 body
  if (context.request.method !== "GET" && context.request.method !== "HEAD") {
    // 獲取原始 body
    const contentType = headers.get("content-type") || "";
    if (contentType.includes("application/json") || contentType.includes("multipart/form-data")) {
       fetchOptions.body = await context.request.arrayBuffer();
    } else {
       fetchOptions.body = context.request.body;
    }
  }

  try {
    console.log(`Proxying ${context.request.method} to: ${backendUrl}`);
    const response = await fetch(backendUrl, fetchOptions);

    // 複製響應 header 並處理 CORS
    const newHeaders = new Headers(response.headers);
    newHeaders.set("Access-Control-Allow-Origin", "*");
    
    return new Response(response.body, {
      status: response.status,
      statusText: response.statusText,
      headers: newHeaders
    });
  } catch (error) {
    console.error(`Proxy Error: ${error.message}`);
    return new Response(JSON.stringify({ error: `Proxy Error: ${error.message}`, url: backendUrl }), { 
      status: 502,
      headers: { "Content-Type": "application/json" }
    });
  }
}
