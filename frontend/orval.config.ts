import { defineConfig } from "orval";

export default defineConfig({
  susdevos: {
    input: {
      target: "./src/lib/schema.json",
    },
    output: {
      mode: "single",
      target: "./src/lib/api/index.ts",
      schemas: "./src/types/api",
      client: "react-query",
      httpClient: "axios",
      allParamsOptional: true,
      override: {
        mutator: {
          path: "./src/lib/orval-mutator.ts",
          name: "axiosInstance",
        },
        query: {
          useQuery: true,
          useMutation: true,
        },
      },
    },
  },
});
