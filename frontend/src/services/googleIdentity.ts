const GOOGLE_IDENTITY_SCRIPT_SRC = 'https://accounts.google.com/gsi/client';

interface GoogleCredentialResponse {
  credential?: string;
}

interface GooglePromptNotification {
  isNotDisplayed?: () => boolean;
  isSkippedMoment?: () => boolean;
}

interface GoogleIdentityApi {
  accounts: {
    id: {
      initialize: (options: {
        client_id: string;
        callback: (response: GoogleCredentialResponse) => void;
      }) => void;
      prompt: (callback?: (notification: GooglePromptNotification) => void) => void;
    };
  };
}

declare global {
  interface Window {
    google?: GoogleIdentityApi;
  }
}

let scriptPromise: Promise<void> | null = null;

const loadGoogleIdentityScript = (): Promise<void> => {
  if (window.google?.accounts?.id) {
    return Promise.resolve();
  }

  if (scriptPromise) {
    return scriptPromise;
  }

  scriptPromise = new Promise<void>((resolve, reject) => {
    const existingScript = document.querySelector<HTMLScriptElement>(
      `script[src="${GOOGLE_IDENTITY_SCRIPT_SRC}"]`
    );
    if (existingScript) {
      existingScript.addEventListener('load', () => resolve(), { once: true });
      existingScript.addEventListener('error', () => reject(new Error('Không thể tải Google Login.')), {
        once: true,
      });
      return;
    }

    const script = document.createElement('script');
    script.src = GOOGLE_IDENTITY_SCRIPT_SRC;
    script.async = true;
    script.defer = true;
    script.onload = () => resolve();
    script.onerror = () => reject(new Error('Không thể tải Google Login.'));
    document.head.appendChild(script);
  });

  return scriptPromise;
};

export const requestGoogleCredential = async (clientId: string): Promise<string> => {
  const trimmedClientId = clientId.trim();
  if (!trimmedClientId) {
    throw new Error('Google login chưa được cấu hình.');
  }

  await loadGoogleIdentityScript();

  return new Promise<string>((resolve, reject) => {
    const identity = window.google?.accounts?.id;
    if (!identity) {
      reject(new Error('Không thể khởi tạo Google Login.'));
      return;
    }

    identity.initialize({
      client_id: trimmedClientId,
      callback: (response) => {
        if (response.credential) {
          resolve(response.credential);
          return;
        }
        reject(new Error('Không nhận được thông tin đăng nhập Google.'));
      },
    });

    identity.prompt((notification) => {
      if (notification?.isNotDisplayed?.() || notification?.isSkippedMoment?.()) {
        reject(new Error('Không thể mở Google Login. Vui lòng thử lại.'));
      }
    });
  });
};
