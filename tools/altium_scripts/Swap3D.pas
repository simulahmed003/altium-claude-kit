{ Swap3D.pas - replace the 3D bodies of the footprints listed in models.csv with STEP models (kit rules LIB-13, TOOL-19).
  Altium embeds each model itself, so the model checksum is right (offline embedding gives red boxes, LESSONS).

  Setup: next to the PcbLib make a folder 3D_KiCad\ (or 3D\) holding the STEP files and models.csv, one line per
  footprint, no header:   footprint name,step file (relative to that folder),rotation Z (deg),offset X (mm),offset Y (mm)
  Example:                RESC1608X55N,R_0603_1608Metric.step,0,0,0
  kit tools/scripts/kicad_models.py writes models.csv for standard IPC-7351B names from a KiCad install.

  Run: open the PcbLib in Altium and make it the active document, then File > Run Script > Browse >
  tools\altium_scripts\Swap3D.pas > SwapKiCad3D. Check the bodies in 3D view (key 3), then save (Ctrl+S).
  Offsets are from the footprint origin. The old bodies are removed; the new body goes on their layer
  (Mechanical 13 when the footprint had none). Live Altium script: one run per library, stop after 2 wedges (TOOL-20). }

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

Procedure SwapKiCad3D;
Var
  Lib      : IPCB_Library;
  Fp       : IPCB_LibComponent;
  Iter     : IPCB_GroupIterator;
  Prim     : IPCB_Primitive;
  Body     : IPCB_ComponentBody;
  Model    : IPCB_Model;
  Lines    : TStringList;
  Old      : TList;
  Dir, L, FpName, StepFile, Report : String;
  Rot, Dx, Dy : Double;
  i, k, Done : Integer;
  Lay      : TLayer;
Begin
  Lib := PCBServer.GetCurrentPCBLibrary;
  If Lib = Nil Then
  Begin
    ShowMessage('Open the PcbLib and make it the active document first.');
    Exit;
  End;
  Dir := ExtractFilePath(Lib.Board.FileName) + '3D_KiCad\';
  If Not FileExists(Dir + 'models.csv') Then
    Dir := ExtractFilePath(Lib.Board.FileName) + '3D\';
  If Not FileExists(Dir + 'models.csv') Then
  Begin
    ShowMessage('models.csv not found in 3D_KiCad\ or 3D\ next to ' + Lib.Board.FileName);
    Exit;
  End;
  Lines := TStringList.Create;
  Lines.LoadFromFile(Dir + 'models.csv');
  Done := 0;
  Report := '';
  PCBServer.PreProcess;
  For i := 0 To Lines.Count - 1 Do
  Begin
    L := Trim(Lines[i]);
    If L = '' Then Continue;
    If Copy(L, 1, 1) = '#' Then Continue;
    FpName := FieldN(L, 0);
    StepFile := Dir + FieldN(L, 1);
    Rot := StrToFloat(FieldN(L, 2));
    Dx := StrToFloat(FieldN(L, 3));
    Dy := StrToFloat(FieldN(L, 4));
    Fp := Lib.GetComponentByName(FpName);
    If Fp = Nil Then
    Begin
      Report := Report + FpName + ': footprint not found' + #13#10;
      Continue;
    End;
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
    { place the KiCad model }
    Body := PCBServer.PCBObjectFactory(eComponentBodyObject, eNoDimension, eCreate_Default);
    Model := Body.ModelFactory_FromFilename(StepFile, False);
    If Model = Nil Then
    Begin
      Report := Report + FpName + ': could not load ' + StepFile + #13#10;
      Continue;
    End;
    Model.SetState(0, 0, Rot, 0);
    Body.Model := Model;
    Body.SetState_FromModel;
    Body.Layer := Lay;
    Body.MoveByXY(Lib.Board.XOrigin + MMsToCoord(Dx), Lib.Board.YOrigin + MMsToCoord(Dy));
    Fp.AddPCBObject(Body);
    PCBServer.SendMessageToRobots(Fp.I_ObjectAddress, c_Broadcast, PCBM_BoardRegisteration, Body.I_ObjectAddress);
    Done := Done + 1;
  End;
  PCBServer.PostProcess;
  Lines.Free;
  Lib.Board.ViewManager_FullUpdate;
  ShowMessage(IntToStr(Done) + ' 3D bodies replaced. Check them in 3D view, then save the library (Ctrl+S).' + #13#10 + Report);
End;
