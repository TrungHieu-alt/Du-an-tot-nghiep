import React, { createContext, useContext, useState, ReactNode } from 'react';

interface ModalContextType {
  isCvModalOpen: boolean;
  openCvModal: () => void;
  closeCvModal: () => void;
  isReqModalOpen: boolean;
  openReqModal: () => void;
  closeReqModal: () => void;
}

const ModalContext = createContext<ModalContextType | undefined>(undefined);

export const ModalProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [isCvModalOpen, setIsCvModalOpen] = useState(false);
  const [isReqModalOpen, setIsReqModalOpen] = useState(false);

  const openCvModal = () => setIsCvModalOpen(true);
  const closeCvModal = () => setIsCvModalOpen(false);

  const openReqModal = () => setIsReqModalOpen(true);
  const closeReqModal = () => setIsReqModalOpen(false);

  return (
    <ModalContext.Provider
      value={{
        isCvModalOpen,
        openCvModal,
        closeCvModal,
        isReqModalOpen,
        openReqModal,
        closeReqModal,
      }}
    >
      {children}
    </ModalContext.Provider>
  );
};

export const useModal = () => {
  const context = useContext(ModalContext);
  if (context === undefined) {
    throw new Error('useModal must be used within a ModalProvider');
  }
  return context;
};
