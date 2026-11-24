import { Suspense } from "react";

import { ShareView } from "./share-view";

// Opened by the phone's Share menu with the shared text in the address, so it is rendered per request.
export default function SharePage() {
  return (
    <Suspense fallback={null}>
      <ShareView />
    </Suspense>
  );
}
