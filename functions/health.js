export async function onRequest(context) {
  const backendUrl = "https://140.245.126.35/health";
  
  try {
    const response = await fetch(backendUrl, {
      headers: { 'Host': 'ewi.paul720810.dpdns.org' }
    });
    const newHeaders = new Headers(response.headers);
    newHeaders.set("Access-Control-Allow-Origin", "*");
    
    return new Response(response.body, {
      status: response.status,
      statusText: response.statusText,
      headers: newHeaders
    });
  } catch (error) {
    return new Response(JSON.stringify({ error: `Proxy Error: ${error.message}` }), { 
      status: 502,
      headers: { "Content-Type": "application/json" }
    });
  }
}
