import { jsPDF } from 'jspdf';
import type { StudyPlan } from '../types';
import { format } from 'date-fns';

const MARGIN = 20;
const PAGE_WIDTH = 210; // A4
const PAGE_HEIGHT = 297;
const CONTENT_WIDTH = PAGE_WIDTH - MARGIN * 2;
const TITLE_SIZE = 22;
const HEADING_SIZE = 14;
const BODY_SIZE = 11;
const MUTED_SIZE = 10;

function sanitizeFilename(name: string): string {
    return name.replace(/[^a-zA-Z0-9-_]/g, '_').slice(0, 80);
}

/**
 * Add text that may wrap; returns the Y position after the text.
 * If text would go past page bottom, adds a new page first.
 */
function addWrappedText(
    doc: jsPDF,
    text: string,
    x: number,
    y: number,
    maxWidth: number,
    fontSize: number
): number {
    doc.setFontSize(fontSize);
    const lines = doc.splitTextToSize(text, maxWidth);
    const lineHeight = fontSize * 0.35; // mm per line
    for (const line of lines) {
        if (y + lineHeight > PAGE_HEIGHT - MARGIN) {
            doc.addPage();
            y = MARGIN;
        }
        doc.text(line, x, y);
        y += lineHeight;
    }
    return y;
}

/**
 * Ensure we have space for at least one line; add new page if needed.
 */
function ensureSpace(doc: jsPDF, y: number, needLines: number = 1): number {
    const lineHeight = BODY_SIZE * 0.35;
    if (y + lineHeight * needLines > PAGE_HEIGHT - MARGIN) {
        doc.addPage();
        return MARGIN;
    }
    return y;
}

export function generateStudyPlanPdf(plan: StudyPlan): jsPDF {
    const doc = new jsPDF({ unit: 'mm', format: 'a4' });
    let y = MARGIN;

    // Title
    doc.setFontSize(TITLE_SIZE);
    doc.setFont('helvetica', 'bold');
    doc.text(`${plan.exam_type} — Study Plan`, MARGIN, y);
    y += 12;

    // Meta line
    doc.setFontSize(MUTED_SIZE);
    doc.setFont('helvetica', 'normal');
    const targetStr = plan.target_date
        ? format(new Date(plan.target_date), 'MMMM d, yyyy')
        : 'No target date';
    doc.text(`Target: ${targetStr}  •  ${plan.daily_hours}h daily  •  ${plan.chapters.length} chapters`, MARGIN, y);
    y += 10;

    const completed = plan.chapters.filter((c) => c.status === 'completed').length;
    const progress = plan.chapters.length ? Math.round((completed / plan.chapters.length) * 100) : 0;
    doc.text(`Progress: ${completed}/${plan.chapters.length} completed (${progress}%)`, MARGIN, y);
    y += 14;

    doc.setFontSize(BODY_SIZE);

    // Chapters
    plan.chapters.forEach((chapter, index) => {
        y = ensureSpace(doc, y, 4);
        doc.setFontSize(HEADING_SIZE);
        doc.setFont('helvetica', 'bold');
        const chapterTitle = `${index + 1}. ${chapter.chapter_name}`;
        y = addWrappedText(doc, chapterTitle, MARGIN, y, CONTENT_WIDTH, HEADING_SIZE);
        y += 2;

        doc.setFontSize(MUTED_SIZE);
        doc.setFont('helvetica', 'normal');
        doc.text(
            `Subject: ${chapter.subject}  •  Est. ${chapter.estimated_hours}h  •  ${chapter.status}`,
            MARGIN,
            y
        );
        y += 6;

        if (chapter.topics && chapter.topics.length > 0) {
            doc.setFontSize(BODY_SIZE);
            doc.setFont('helvetica', 'bold');
            doc.text('Topics:', MARGIN, y);
            y += 5;
            doc.setFont('helvetica', 'normal');
            chapter.topics.forEach((topic) => {
                y = ensureSpace(doc, y);
                y = addWrappedText(doc, `• ${topic}`, MARGIN + 4, y, CONTENT_WIDTH - 4, BODY_SIZE);
                y += 1;
            });
        }
        y += 8;
    });

    return doc;
}

export function downloadStudyPlanPdf(plan: StudyPlan): void {
    const doc = generateStudyPlanPdf(plan);
    const name = sanitizeFilename(plan.exam_type);
    doc.save(`${name}_study_plan.pdf`);
}
