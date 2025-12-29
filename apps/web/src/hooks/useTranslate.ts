import { useCallback, useState } from "react";

import { translateKoToEn } from "../lib/api";

export interface TranslateState {
  inputText: string;
  outputText: string;
  isLoading: boolean;
  error: string | null;
}

export function useTranslate() {
  const [state, setState] = useState<TranslateState>({
    inputText: "",
    outputText: "",
    isLoading: false,
    error: null,
  });

  const setInputText = useCallback((text: string) => {
    setState((current) => ({ ...current, inputText: text, error: null }));
  }, []);

  const translate = useCallback(async () => {
    if (!state.inputText.trim()) {
      return;
    }

    setState((current) => ({ ...current, isLoading: true, error: null }));

    try {
      const response = await translateKoToEn(state.inputText);
      setState((current) => ({
        ...current,
        outputText: response.translatedText,
        isLoading: false,
      }));
    } catch (error) {
      setState((current) => ({
        ...current,
        error: error instanceof Error ? error.message : "Translation failed",
        isLoading: false,
      }));
    }
  }, [state.inputText]);

  const copyToClipboard = useCallback(async () => {
    if (state.outputText) {
      await navigator.clipboard.writeText(state.outputText);
      return true;
    }
    return false;
  }, [state.outputText]);

  const clear = useCallback(() => {
    setState({ inputText: "", outputText: "", isLoading: false, error: null });
  }, []);

  return {
    ...state,
    setInputText,
    translate,
    copyToClipboard,
    clear,
  };
}
