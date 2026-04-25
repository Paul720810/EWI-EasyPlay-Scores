export async function onRequest(context) {
  const url = new URL(context.request.url);
  
  // 將所有 /api/* 的請求轉發到 OCI 後端
  // 您的後端目前在 http://140.245.126.35:8001
  const backendUrl = `http://140.245.126.35:8001${url.pathname}${url.search}`;
  
  console.log(`Proxying request to: ${backendUrl}`);
  
  // 複製原始請求的 header，但移除 Host 以避免衝突
  const headers = new Headers(context.request.headers);
  headers.delete("Host");

  try {
    const response = await fetch(backendUrl, {
      method: context.request.method,
      headers: headers,
      body: context.request.body,
      redirect: 'follow'
    });

    // 返回後端的響應
    return response;
  } catch (error) {
    return new Response(`Proxy Error: ${error.message}`, { status: 502 });
  }
}
