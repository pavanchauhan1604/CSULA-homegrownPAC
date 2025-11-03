# CSULA PDF Accessibility Checker - Documentation Index

**Last Updated:** October 27, 2025

This index helps you find the right documentation for your needs.

---

## 🎯 What Do You Want to Do?

### I want to... **install the software**
→ Read: **[INSTALLATION_GUIDE.md](INSTALLATION_GUIDE.md)**
- Installing Python 3.11+
- Installing VeraPDF
- Installing Python packages
- Troubleshooting installation issues

---

### I want to... **set up and run the checker**
→ Read: **[COMPLETE_SETUP_GUIDE.md](COMPLETE_SETUP_GUIDE.md)**
- Initial configuration
- Editing config.py
- Running the complete workflow
- Understanding results
- Production deployment

---

### I want to... **quickly look up a command**
→ Use: **[QUICK_REFERENCE.md](QUICK_REFERENCE.md)**
- Common commands
- Database queries
- Troubleshooting table
- Quick fixes

---

### I want to... **understand what changed**
→ Read: **[REORGANIZATION_SUMMARY.md](REORGANIZATION_SUMMARY.md)**
- What's new in the folder structure
- Documentation changes
- Migration notes
- Verification steps

---

## 📚 All Documentation Files

| File | Purpose | When to Use |
|------|---------|-------------|
| **INSTALLATION_GUIDE.md** | Software installation | First time setup, new machine |
| **COMPLETE_SETUP_GUIDE.md** | Full setup & usage guide | Complete reference |
| **QUICK_REFERENCE.md** | Commands & troubleshooting | Quick lookup |
| **REORGANIZATION_SUMMARY.md** | Project structure changes | Understanding new layout |

---

## 🚀 Quick Start Path

**First Time User:**
1. ✅ Read [INSTALLATION_GUIDE.md](INSTALLATION_GUIDE.md)
2. ✅ Read [COMPLETE_SETUP_GUIDE.md](COMPLETE_SETUP_GUIDE.md) sections 1-4
3. ✅ Run: `./scripts/fresh_start.sh && ./scripts/run_workflow.sh`
4. ✅ Bookmark [QUICK_REFERENCE.md](QUICK_REFERENCE.md) for daily use

**Returning User:**
1. ✅ Use [QUICK_REFERENCE.md](QUICK_REFERENCE.md) for commands
2. ✅ Refer to [COMPLETE_SETUP_GUIDE.md](COMPLETE_SETUP_GUIDE.md) as needed

---

## 📂 Where Are Things?

### Scripts
All executable scripts are in: `../scripts/`
- `run_workflow.sh` - Complete workflow
- `fresh_start.sh` - Clean and reset
- `check_progress.sh` - Monitor progress
- `setup_test_environment.py` - Database setup

### Configuration
Main config file: `../config.py`
- Edit domains, email, settings here

### Results
- Excel reports: `../output/scans/{domain}/`
- Email previews: `../output/emails/`
- Database: `../drupal_pdfs.db`

### Old Documentation
Archived for reference: `archive/`
- All previous documentation files preserved

---

## 🆘 Help! I'm Lost!

### Common Questions

**Q: Where do I start?**  
A: Read [INSTALLATION_GUIDE.md](INSTALLATION_GUIDE.md) first, then [COMPLETE_SETUP_GUIDE.md](COMPLETE_SETUP_GUIDE.md)

**Q: How do I run the checker?**  
A: `./scripts/fresh_start.sh && ./scripts/run_workflow.sh`

**Q: Where is the old documentation?**  
A: In `setup/archive/` folder

**Q: Where are the scripts?**  
A: In `scripts/` folder at project root

**Q: How do I configure domains?**  
A: Edit `config.py` at project root

**Q: Where are the results?**  
A: `output/scans/` for Excel, `output/emails/` for HTML

**Q: What if something breaks?**  
A: Check [QUICK_REFERENCE.md](QUICK_REFERENCE.md) troubleshooting section

---

## 📖 Documentation Reading Order

### For Installation (First Time)
1. INSTALLATION_GUIDE.md (30 minutes)
2. COMPLETE_SETUP_GUIDE.md - Sections 1-3 (15 minutes)
3. QUICK_REFERENCE.md - Skim through (5 minutes)

### For Configuration
1. COMPLETE_SETUP_GUIDE.md - Section 3 (10 minutes)
2. Edit `config.py` (5 minutes)
3. QUICK_REFERENCE.md - Configuration section (5 minutes)

### For Running
1. COMPLETE_SETUP_GUIDE.md - Section 4 (15 minutes)
2. Run workflow (30-90 minutes execution)
3. COMPLETE_SETUP_GUIDE.md - Section 5 (10 minutes)

### For Troubleshooting
1. QUICK_REFERENCE.md - Troubleshooting table (immediate)
2. COMPLETE_SETUP_GUIDE.md - Section 6 (as needed)
3. INSTALLATION_GUIDE.md - Installation issues (if needed)

---

## 🎓 Learning Path

### Beginner
- [ ] Install software (INSTALLATION_GUIDE.md)
- [ ] Read sections 1-4 of COMPLETE_SETUP_GUIDE.md
- [ ] Run your first scan
- [ ] Review results

### Intermediate
- [ ] Configure multiple domains
- [ ] Understand database structure
- [ ] Query results with SQL
- [ ] Schedule automated runs

### Advanced
- [ ] Modify config for production
- [ ] Customize report generation
- [ ] Integrate with other systems
- [ ] Contribute improvements

---

## 📊 Documentation Statistics

- **Total guides:** 4 main documents
- **Total pages:** ~40 pages equivalent
- **Reading time:** ~60 minutes (all docs)
- **Quick start time:** 5 minutes (with QUICK_REFERENCE.md)

---

## 🔍 Search Tips

**Looking for:**
- Installation problems → INSTALLATION_GUIDE.md
- Configuration options → COMPLETE_SETUP_GUIDE.md Section 3
- Command syntax → QUICK_REFERENCE.md
- Database queries → QUICK_REFERENCE.md
- Error messages → COMPLETE_SETUP_GUIDE.md Section 6
- Project changes → REORGANIZATION_SUMMARY.md

---

**Ready to start?** Begin with: [INSTALLATION_GUIDE.md](INSTALLATION_GUIDE.md)
