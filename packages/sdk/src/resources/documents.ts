import type { OpenBiometrics } from '../client';
import type { DocumentScanResponse, OCRResult, MRZResult, VerifyResponse } from '../types';

export class Documents {
  constructor(private client: OpenBiometrics) {}

  /**
   * Scan a document image — detect document type, extract OCR text, and MRZ data.
   *
   * @example
   * ```ts
   * const result = await ob.documents.scan(idCardImage);
   * console.log(result.document_type, result.mrz?.parsed.surname);
   * ```
   */
  async scan(image: Blob | ArrayBuffer | Uint8Array): Promise<DocumentScanResponse> {
    const form = this.client.createForm(image);
    return this.client.request<DocumentScanResponse>('POST', '/documents/scan', form);
  }

  /**
   * Extract text from a document image using OCR.
   */
  async ocr(image: Blob | ArrayBuffer | Uint8Array): Promise<OCRResult> {
    const form = this.client.createForm(image);
    return this.client.request<OCRResult>('POST', '/documents/ocr', form);
  }

  /**
   * Read and parse the MRZ zone from an identity document.
   */
  async mrz(image: Blob | ArrayBuffer | Uint8Array): Promise<MRZResult> {
    const form = this.client.createForm(image);
    return this.client.request<MRZResult>('POST', '/documents/mrz', form);
  }

  /**
   * Verify a face against the photo on a document.
   *
   * @example
   * ```ts
   * const { is_match, similarity } = await ob.documents.verify(selfie, idCardImage);
   * ```
   */
  async verify(
    faceImage: Blob | ArrayBuffer | Uint8Array,
    documentImage: Blob | ArrayBuffer | Uint8Array,
  ): Promise<VerifyResponse> {
    const form = new FormData();
    const toBlob = (img: Blob | ArrayBuffer | Uint8Array) =>
      img instanceof Blob ? img : new Blob([img as BlobPart]);
    form.append('face_image', toBlob(faceImage), 'face.jpg');
    form.append('document_image', toBlob(documentImage), 'document.jpg');
    return this.client.request<VerifyResponse>('POST', '/documents/verify', form);
  }
}
