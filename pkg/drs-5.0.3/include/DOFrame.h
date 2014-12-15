#ifndef __DOFrame__
#define __DOFrame__

// $Id: DOFrame.h 21266 2014-02-12 16:05:28Z ritt $

/**
@file
Subclass of DOFrame_fb, which is generated by wxFormBuilder.
*/

class EPThread;

/** Implementing DOFrame_fb */
class DOFrame : public DOFrame_fb
{
protected:
   void LoadConfig(char *error, int size);
   void SaveConfig(void);

   // Handlers for DOFrame_fb events.
   void OnConfig(wxCommandEvent& event);
   void OnMeasure(wxCommandEvent& event);
   void OnDisplay(wxCommandEvent& event);
   void OnPrint(wxCommandEvent& event);
   void OnExit(wxCommandEvent& event);
   void OnAbout(wxCommandEvent& event);
   void OnSave(wxCommandEvent& event);
   void OnTrigger(wxCommandEvent& event);
   void OnTrgButton(wxCommandEvent& event);
   void OnTrgLevelChange(wxScrollEvent& event);
   void OnTrgDelayChange(wxScrollEvent& event);
   void OnChnOn(wxCommandEvent& event);
   void OnPosChange(wxScrollEvent& event);
   void OnScaleChange(wxCommandEvent& event);
   void OnHScaleChange(wxCommandEvent& event);
   void OnHOffsetChange(wxScrollEvent& event);
   void OnZero(wxMouseEvent& event);
   void OnTimer(wxTimerEvent& event);
   void OnCursor(wxCommandEvent& event);
   void OnSnap(wxCommandEvent& event);

   void ProcessEvents(void);
   
public:
   DOFrame( wxWindow* parent );
   ~DOFrame();

   ConfigDialog *GetConfigDialog() { return m_configDialog; }
   wxColor GetColor(int i, bool p) { return p ? m_pcolor[i]: m_color[i]; }
   int GetAcqPerSecond()   { return m_acqPerSecond; }
   double GetTrgLevel(int i) { return m_trgLevel[m_board][i]; }
   int GetTrgMode()        { return m_trgMode[m_board]; }
   int GetTrgSource(int b) { return m_trgSource[b]; }
   int GetTrgPolarity()    { return m_trgNegative[m_board]; }
   double GetTrgDelay()       { return m_trgDelayNs[m_board]; }
   int GetTriggerConfig()  { return m_trgConfig[m_board]; }
   double GetTrgPosition(int board);
   time_t GetLastTriggerUpdate() { return m_lastTriggerUpdate; }
   bool IsIdle();
   bool GetRearm()         { return m_rearm; }
   bool GetTrgCorr()       { return m_trgCorr; }
   MXML_WRITER *GetWFFile() { return m_WFFile; }
   int GetWFfd()           { return m_WFfd; }
   int GetNSaved()         { return m_nSaved; }
   int GetNSaveMax()         { return m_nSaveMax; }
   void SetRearm(bool f)   { m_rearm = f; }
   void SetSamplingSpeed(double speed);
   double GetReqSamplingSpeed() { return m_reqSamplingSpeed; }
   double GetActSamplingSpeed();
   void SetTrgLevel(int i, double value);
   Osci *GetOsci()         { return m_osci; }
   void SetPaintMode(int pm) { m_screen->SetPaintMode(pm); }
   void SetDisplayDateTime(bool flag);
   void SetDisplayShowGrid(bool flag);
   void SetDisplayLines(bool flag);
   void SetDisplayMode(int mode, int n);
   void SetDisplayScalers(bool flag);
   void SetDisplayCalibrated(bool flag);
   void SetDisplayCalibrated2(bool flag);
   void SetDisplayTCalOn(bool flag);
   void SetDisplayTrgCorr(bool flag);
   void SetDisplayRotated(bool flag);
   void SetCursorA(bool flag);
   void SetCursorB(bool flag);
   bool IsCursorA()        { return m_cursorA; }
   bool IsCursorB()        { return m_cursorB; }
   int  ActiveCursor()     { return m_actCursor; }
   void SetActiveCursor(int c) { m_actCursor = c; }
   bool IsSnap()           { return m_snap; }
   void ToggleControls();
   void SetMeasurement(int id, bool flag);
   void SetMathDisplay(int id, bool flag);
   void SetTriggerConfig(int id, bool flag);
   void SetTriggerSource(int b, int source);
   void SetTriggerPolarity(int b, bool negative);
   void SetStat(bool flag);
   void SetHist(bool flag);
   void SetStatNStat(int n);
   int GetNStat() { return m_nStat; }
   void SetIndicator(bool flag);
   void SetClkOn(bool flag){ m_clkOn = flag; m_osci->SetClkOn(flag) ; }
   bool GetClkOn()         { return m_clkOn; }
   void SelectBoard(int board);
   int GetCurrentBoard()   { return m_board; }
   void SetMultiBoard(bool flag);
   void SetSplitMode(bool flag) { m_splitMode = flag; m_screen->SetSplitMode(flag); }
   bool GetMultiBoard()    { return m_multiBoard; }
   void SetSource(int board, int firstChannel, int chnSection);
   void SetRefclk(int board, bool flag);
   bool GetRefclk()        { return m_refClk > 0; }
   void SetRange(double range){ m_range[m_board] = range; }
   double GetRange()           { return m_range[m_board]; }
   void SetSpikeRemoval(bool flag) { m_spikeRemoval = flag; m_osci->SetSpikeRemoval(flag); }
   bool GetSpikeRemovel()    { return m_spikeRemoval; }
   void StatReset();
   bool IsStat()             { return m_stat; }
   bool IsHist()             { return m_hist; }
   bool IsIndicator()        { return m_indicator; }
   wxTimer *GetTimer()       { return m_timer; }
   void UpdateStatusBar();
   bool IsFirst()            { return m_first; }
   void SetFreqLock(bool flag) { m_freqLocked = flag; }
   bool IsFreqLocked()       { return m_freqLocked; }
   void SetProgress(int prog) { m_progress = prog; }
   int  GetProgress()        { return m_progress; }
   void UpdateWaveforms();
   void ClearWaveforms();
   void UpdateControls();
   float *GetWaveform(int b, int c);
   float *GetTime(int b, int c);
   void EnableTriggerConfig(bool flag);

   bool IsMeasurement(int m, int chn);
   double GetMeasurement(int idx, double *x, double *y, int n);
   wxString GetMeasurementName(int idx) { return m_measurement[idx][0]->GetName(); }
   Measurement* GetMeasurement(int idx, int chn);
   void EvaluateMeasurements(void);
   void ChangeHScale(int delta);
   void RecalculateHOffset(double trgFrac);
   void CloseWFFile(bool errorFlag);
   void SetSaveBtn(wxString l, wxString t);
   void IncrementAcquisitions();
   void IncrementSaved();
   void EnableEPThread(bool flag);


private:
   DECLARE_EVENT_TABLE()

   DOScreen       *m_screen;
   Osci           *m_osci;
   Measurement    *m_measurement[Measurement::N_MEASUREMENTS][4];
   bool           m_measFlag[Measurement::N_MEASUREMENTS][4];
   bool           m_stat;
   bool           m_hist;
   bool           m_indicator;
   bool           m_first;

   wxTimer        *m_timer;
   ConfigDialog   *m_configDialog;
   MeasureDialog  *m_measureDialog;
   TriggerDialog  *m_triggerDialog;
   DisplayDialog  *m_displayDialog;
   EPThread       *m_epthread;

   float          m_time[MAX_N_BOARDS][4][2048];
   float          m_waveform[MAX_N_BOARDS][4][2048];
   char           m_xmlError[256];
   bool           m_running;
   bool           m_single;
   bool           m_rearm;
   double         m_reqSamplingSpeed;
   bool           m_freqLocked;
   bool           m_oldIdle;

   double         m_trgLevel[MAX_N_BOARDS][4];
   int            m_trgMode[MAX_N_BOARDS];
   bool           m_trgNegative[MAX_N_BOARDS];
   int            m_trgSource[MAX_N_BOARDS];
   int            m_trgDelay[MAX_N_BOARDS];
   double         m_trgDelayNs[MAX_N_BOARDS];
   int            m_trgConfig[MAX_N_BOARDS];
   bool           m_refClk[MAX_N_BOARDS];
   bool           m_trgCorr;

   int            m_HScale[MAX_N_BOARDS];
   int            m_HOffset[MAX_N_BOARDS];

   bool           m_chnOn[MAX_N_BOARDS][4];
   int            m_chnOffset[MAX_N_BOARDS][4];
   int            m_chnScale[MAX_N_BOARDS][4];
   bool           m_clkOn;
   double         m_range[MAX_N_BOARDS];
   bool           m_spikeRemoval;
   bool           m_displayScalers;

   wxColour       m_color[5];
   wxColour       m_pcolor[5];

   int            m_acquisitions;
   wxStopWatch    m_stopWatch;
   wxStopWatch    m_stopWatch1;
   int            m_acqPerSecond;
   int            m_nStat;

   time_t         m_lastTriggerUpdate;

   MXML_WRITER    *m_WFFile;
   int            m_WFfd;
   int            m_nSaved;
   int            m_nSaveMax;
   int            m_actCursor;
   bool           m_cursorA;
   bool           m_cursorB;
   bool           m_snap;

   bool           m_hideControls;

   int            m_board;
   int            m_firstChannel;
   int            m_chnSection;
   bool           m_multiBoard;
   bool           m_splitMode;

   int            m_progress;
};

#endif // __DOFrame__
