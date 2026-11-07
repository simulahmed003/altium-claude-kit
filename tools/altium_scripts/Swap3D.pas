{ Swap3D.pas - replace the 3D bodies of the footprints listed in models.csv with STEP models (kit rules LIB-13, TOOL-19).
  Altium embeds each model itself, so the model checksum is right (offline embedding gives red boxes, LESSONS).

  Setup: next to the PcbLib make a folder 3D_KiCad\ (or 3D\) holding the STEP files and models.csv, one line per
  footprint, no header:   footprint name,step file (relative to that folder),rotation Z (deg),offset X (mm),offset Y (mm)
  Example:                RESC1608X55N,R_0603_1608Metric.step,0,0,0
  kit tools/scripts/kicad_models.py writes models.csv for standard IPC-7351B names from a KiCad install.

  Run: open the PcbLib in Altium and make it the active document, then File > Run Script > Browse >
  tools\altium_scripts\Swap3D.pas > SwapKiCad3D. Check the bodies in 3D view (key 3), then save (Ctrl+S).
  Offsets are from the footprint origin. The old bodies are removed; the new body goes on their layer
  (Mechanical 13 when the footprint had none). Live Altium script: one run per library, stop after 2 wedges (TOOL-20).
  No message boxes (an agent run would wait on them, TOOL-21): the result goes to Swap3D_log.txt in the models folder
  (C:\Users\Public\ when no PcbLib is active). A footprint that raises an error is logged and skipped. }

Function FieldN(S : String; N : Integer) : String;
Var
  i, k : Integer;
Begin
  k := 0;
  Result := '';
  For i := 1 To Length(S) Do
  Begin
    If S[i] = ',' Then
      k := k + 1
    Else If k = N Then
      Result := Result + S[i];
  End;
End;

Function SwapOne(Lib : IPCB_Library; L, Dir : String) : String;
Var
  Fp       : IPCB_LibComponent;
  Iter     : IPCB_GroupIterator;
  Prim     : IPCB_Primitive;
  Body     : IPCB_ComponentBody;
  Model    : IPCB_Model;
  Old      : TList;
  FpName, StepFile : String;
  Rot, Dx, Dy : Double;
  k        : Integer;
  Lay      : TLayer;
Begin
  FpName := FieldN(L, 0);
  StepFile := Dir + FieldN(L, 1);
  Rot := StrToFloat(FieldN(L, 2));
  Dx := StrToFloat(FieldN(L, 3));
  Dy := StrToFloat(FieldN(L, 4));
  Fp := Lib.GetComponentByName(FpName);
  If Fp = Nil Then
  Begin
    Result := FpName + ': footprint not found';
    Exit;
  End;
  If Not FileExists(StepFile) Then
  Begin
    Result := FpName + ': STEP file missing ' + StepFile;
    Exit;
  End;
  { make it the current footprint: only then are its coordinates relative to the board origin (TOOL-19);
    without this the body of every other footprint landed 1270 mm away (PC test 2026-11-07) }
  Lib.SetState_CurrentComponent(Fp);
  { collect and remove the old 3D bodies }
  Lay := eMechanical13;
  Old := TList.Create;
  Iter := Fp.GroupIterator_Create;
  Iter.AddFilter_ObjectSet(MkSet(eComponentBodyObject));
  Prim := Iter.FirstPCBObject;
  While Prim <> Nil Do
  Begin
    Old.Add(Prim);
    Prim := Iter.NextPCBObject;
  End;
  Fp.GroupIterator_Destroy(Iter);
  If Old.Count > 0 Then Lay := Old[0].Layer;
  For k := 0 To Old.Count - 1 Do
    Fp.RemovePCBObject(Old[k]);
  Old.Free;
  { place the model }
  Body := PCBServer.PCBObjectFactory(eComponentBodyObject, eNoDimension, eCreate_Default);
  Model := Body.ModelFactory_FromFilename(StepFile, False);
  If Model = Nil Then
  Begin
    Result := FpName + ': could not load ' + StepFile;
    Exit;
  End;
  Model.SetState(0, 0, Rot, 0);
  Body.Model := Model;
  Body.SetState_FromModel;
  Body.Layer := Lay;
  Body.MoveByXY(Lib.Board.XOrigin + MMsToCoord(Dx), Lib.Board.YOrigin + MMsToCoord(Dy));
  Fp.AddPCBObject(Body);
  PCBServer.SendMessageToRobots(Fp.I_ObjectAddress, c_Broadcast, PCBM_BoardRegisteration, Body.I_ObjectAddress);
  Result := '';
End;

Procedure SwapKiCad3D;
Var
  Lib      : IPCB_Library;
  Lines, Log : TStringList;
  Dir, L, R, LogDir : String;
  i, Done  : Integer;
Begin
  Log := TStringList.Create;
  Done := 0;
  Lib := PCBServer.GetCurrentPCBLibrary;
  If Lib = Nil Then
    Log.Add('STOP: no PcbLib is the active document (open it and make it active first)')
  Else
  Begin
    Dir := ExtractFilePath(Lib.Board.FileName) + '3D_KiCad\';
    If Not FileExists(Dir + 'models.csv') Then
      Dir := ExtractFilePath(Lib.Board.FileName) + '3D\';
    If Not FileExists(Dir + 'models.csv') Then
      Log.Add('STOP: models.csv not found in 3D_KiCad\ or 3D\ next to ' + Lib.Board.FileName)
    Else
    Begin
      Lines := TStringList.Create;
      Lines.LoadFromFile(Dir + 'models.csv');
      PCBServer.PreProcess;
      Try
        For i := 0 To Lines.Count - 1 Do
        Begin
          L := Trim(Lines[i]);
          If (L <> '') And (Copy(L, 1, 1) <> '#') Then
          Begin
            Try
              R := SwapOne(Lib, L, Dir);
            Except
              R := FieldN(L, 0) + ': script error, footprint skipped';
            End;
            If R = '' Then
              Done := Done + 1
            Else
              Log.Add(R);
          End;
        End;
      Finally
        PCBServer.PostProcess;
        Lines.Free;
      End;
      Lib.Board.ViewManager_FullUpdate;
      { mark the library modified, so Ctrl+S saves it }
      If Client.CurrentView <> Nil Then
        Client.CurrentView.OwnerDocument.Modified := True;
    End;
  End;
  Log.Insert(0, IntToStr(Done) + ' 3D bodies replaced. Check them in 3D view (key 3), then save the library (Ctrl+S).');
  LogDir := Dir;
  If LogDir = '' Then LogDir := 'C:\Users\Public\';
  Log.SaveToFile(LogDir + 'Swap3D_log.txt');
  Log.Free;
End;
