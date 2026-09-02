import Link from "next/link";
import { FileQuestion } from "lucide-react";

export default function CaseNotFound() {
  return (
    <div className="grid flex-1 place-items-center p-10">
      <div className="text-center">
        <div className="mx-auto grid h-12 w-12 place-items-center rounded-xl bg-muted text-muted-foreground">
          <FileQuestion className="h-6 w-6" />
        </div>
        <p className="mt-4 text-lg font-semibold">Recovery case not found</p>
        <Link href="/cases" className="mt-2 inline-block text-sm text-primary hover:underline">
          Back to all cases
        </Link>
      </div>
    </div>
  );
}
