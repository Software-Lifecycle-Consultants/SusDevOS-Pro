/**
 * Orval mutator — minimal axios instance for code generation.
 * The real runtime instance (with auth interceptors) is in axios-instance.ts.
 * Orval just needs a callable function with this signature.
 */
import axios, { type AxiosRequestConfig } from "axios";

const instance = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000",
  withCredentials: true,
});

export const axiosInstance = <T>(config: AxiosRequestConfig): Promise<T> => {
  return instance(config).then((r) => r.data);
};

export default axiosInstance;
