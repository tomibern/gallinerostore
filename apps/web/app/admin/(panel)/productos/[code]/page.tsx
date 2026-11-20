import { ProductEditorPage } from "@/components/admin/product-editor-page";

export default async function EditProductPage({ params }: { params: Promise<{ code: string }> }) {
  const { code } = await params;
  return <ProductEditorPage code={decodeURIComponent(code)} />;
}
