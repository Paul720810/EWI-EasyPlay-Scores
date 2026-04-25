export async function onRequest(context) {
  const backendUrl = "http://140.245.126.35:8001/health";
  
  try {
    const response = await fetch(backendUrl);
    return response;
  } catch (error) {
    return new Response(`Proxy Error: ${error.message}`, { status: 502 });
  }
}
